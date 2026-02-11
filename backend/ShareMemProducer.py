import ctypes
import os
import time
from multiprocessing import shared_memory


class _AtomicU32:
    def __init__(self, buf, offset: int):
        """在共享内存缓冲区指定偏移处绑定一个 32 位无符号整型视图。"""
        if offset % 4 != 0:
            raise RuntimeError(f"uint32 offset must be 4-byte aligned: {offset}")
        self._cell = ctypes.c_uint32.from_buffer(buf, offset)

    def load(self) -> int:
        """读取当前 uint32 值，并在读取前执行内存屏障保证可见性。"""
        _memory_barrier()
        return int(self._cell.value) & 0xFFFFFFFF

    def store(self, value: int) -> None:
        """写入 uint32 值，并在写入后执行内存屏障发布写入结果。"""
        self._cell.value = int(value) & 0xFFFFFFFF
        _memory_barrier()


if os.name == "nt":
    _FLUSH_PROCESS_WRITE_BUFFERS = ctypes.windll.kernel32.FlushProcessWriteBuffers
    _FLUSH_PROCESS_WRITE_BUFFERS.argtypes = []
    _FLUSH_PROCESS_WRITE_BUFFERS.restype = None

    def _memory_barrier() -> None:
        """Windows 下使用系统 API 刷新写缓冲，提供跨进程可见性。"""
        _FLUSH_PROCESS_WRITE_BUFFERS()

else:

    def _memory_barrier() -> None:
        """非 Windows 平台占位实现（当前工程主要运行在 Windows）。"""
        return None


class ShareMemProducer:
    MAGIC = 0x499602D2
    HEADER_SIZE = 64
    MAX_RING_FRAMES = 100000
    MAX_SHARED_MEMORY_SIZE = 100 * 1024 * 1024

    OFFSET_MAGIC = 0
    OFFSET_FRAME_LEN = 4
    OFFSET_RING_FRAMES = 8
    OFFSET_TOTAL_FRAMES = 12
    OFFSET_WRITE_FRAMES = 16
    OFFSET_READ_FRAMES = 20

    def __init__(self, frame_len: int, total_frames: int, wait_seconds: float = 0.001):
        """创建共享内存并初始化生产者头部字段。"""
        if frame_len <= 0:
            raise RuntimeError(f"invalid frame_len: {frame_len}")
        if total_frames < 0:
            raise RuntimeError(f"invalid total_frames: {total_frames}")
        if frame_len > 0xFFFFFFFF or total_frames > 0xFFFFFFFF:
            raise RuntimeError("frame_len/total_frames exceed uint32 range")

        self.frame_len = int(frame_len)
        self.total_frames = int(total_frames)
        self.wait_seconds = wait_seconds
        self._closed = False

        self.ring_frames = self._calc_ring_frames()
        self.size = self.HEADER_SIZE + self.ring_frames * self.frame_len
        self.shm = None
        self.buf = None
        self._zero_frame = bytes(self.frame_len)
        self._write_frames_atomic = None
        self._read_frames_atomic = None
        self._total_frames_atomic = None

        try:
            self.shm = shared_memory.SharedMemory(create=True, size=self.size)
            self.buf = self.shm.buf
            self._init_header()
        except Exception:
            self.close()
            raise

    def _calc_ring_frames(self) -> int:
        """按“100000 帧 + 100MB 上限”规则计算环形缓冲帧数。"""
        actual_size = self.HEADER_SIZE + self.total_frames * self.frame_len
        if self.total_frames <= self.MAX_RING_FRAMES and actual_size <= self.MAX_SHARED_MEMORY_SIZE:
            ring_frames = self.total_frames
        else:
            cap_size_with_max_ring = self.HEADER_SIZE + self.frame_len * self.MAX_RING_FRAMES
            if cap_size_with_max_ring <= self.MAX_SHARED_MEMORY_SIZE:
                ring_frames = self.MAX_RING_FRAMES
            else:
                ring_frames = (self.MAX_SHARED_MEMORY_SIZE - self.HEADER_SIZE) // self.frame_len

        if ring_frames <= 0:
            raise RuntimeError(f"frame_len too large for shared memory cap: frame_len={self.frame_len}, " f"max_size={self.MAX_SHARED_MEMORY_SIZE}")
        if ring_frames > 0xFFFFFFFF:
            raise RuntimeError(f"ring_frames exceed uint32 range: {ring_frames}")
        return int(ring_frames)

    @property
    def token(self) -> str:
        """返回共享内存 token（供消费者进程打开同一块共享内存）。"""
        return self.shm.name

    def _write_u32(self, offset: int, value: int) -> None:
        """按小端序向共享内存头部写入 uint32。"""
        self.buf[offset : offset + 4] = int(value & 0xFFFFFFFF).to_bytes(4, "little")

    def _init_header(self) -> None:
        """初始化共享内存头部（magic、帧长、环形帧数与读写计数器）。"""
        self.buf[:] = b"\x00" * self.size
        self._write_u32(self.OFFSET_MAGIC, self.MAGIC)
        self._write_u32(self.OFFSET_FRAME_LEN, self.frame_len)
        self._write_u32(self.OFFSET_RING_FRAMES, self.ring_frames)

        self._total_frames_atomic = _AtomicU32(self.buf, self.OFFSET_TOTAL_FRAMES)
        self._write_frames_atomic = _AtomicU32(self.buf, self.OFFSET_WRITE_FRAMES)
        self._read_frames_atomic = _AtomicU32(self.buf, self.OFFSET_READ_FRAMES)
        self._total_frames_atomic.store(self.total_frames)
        self._write_frames_atomic.store(0)
        self._read_frames_atomic.store(0)

    def write_frame(self, frame: bytes) -> None:
        """向环形缓冲写入一帧；满缓冲时阻塞等待可写槽位。"""
        frame_view = memoryview(frame)
        frame_len = frame_view.nbytes
        if frame_len > self.frame_len:
            raise RuntimeError(f"frame too large: {frame_len} > {self.frame_len}")

        while True:
            write_frames = self._write_frames_atomic.load()
            read_frames = self._read_frames_atomic.load()
            if (write_frames - read_frames) < self.ring_frames:
                break
            time.sleep(self.wait_seconds)

        slot = write_frames % self.ring_frames
        pos = self.HEADER_SIZE + slot * self.frame_len
        end = pos + self.frame_len

        if frame_len == self.frame_len:
            self.buf[pos:end] = frame_view
        else:
            self.buf[pos:end] = self._zero_frame
            self.buf[pos : pos + frame_len] = frame_view

        # Publish frame visibility after payload write.
        self._write_frames_atomic.store(write_frames + 1)

    def close(self) -> None:
        """释放共享内存视图与句柄，并尝试 unlink 清理命名对象。"""
        if self._closed:
            return
        self._closed = True

        self._total_frames_atomic = None
        self._write_frames_atomic = None
        self._read_frames_atomic = None
        self._zero_frame = None
        self.buf = None

        if self.shm is not None:
            try:
                self.shm.close()
            finally:
                try:
                    self.shm.unlink()
                except FileNotFoundError:
                    pass
                self.shm = None

    def __enter__(self):
        """支持 with 语法：进入上下文直接返回实例。"""
        return self

    def __exit__(self, exc_type, exc, tb):
        """支持 with 语法：退出上下文时自动释放共享内存资源。"""
        self.close()
        return False
