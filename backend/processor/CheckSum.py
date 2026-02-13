from backend.processor.ProcessorBase import ProcessorBase

import libscrc
import ctypes


class CheckSumBase(ProcessorBase):
    """校验和基类"""

    def __init__(self):
        super().__init__()
        self.ck_start = 0
        self.ck_size = 0

    def load(self, xml_node):
        self.priority = -99  # 校验和默认优先级最低
        super().load(xml_node)

        self._load_byteorder(xml_node)

        self.ck_start = int(xml_node.attrib["ck_start"], 0)
        self.ck_size = int(xml_node.attrib["ck_size"], 0)

        # 定长帧检查校验范围
        if self.package.variable_len_frame is False:
            if self.size <= 0 or self.size > 8:
                raise RuntimeError(f"{self.package.name}-{self.name}: return size error")
            if self.ck_size == 0:
                raise RuntimeError(f"{self.package.name}-{self.name} error: ck_size == 0")
            if (self.ck_start + self.ck_size) > self.package.max_size:
                raise RuntimeError(f"{self.package.name}-{self.name} error: ck_start + ck_size > max_size")

    def apply_var_offset(self, var_len: int, var_offset: int, var_size: int):
        super().apply_var_offset(var_len, var_offset, var_size)
        self.ck_size += var_len

        if self.ck_start < 0:
            raise RuntimeError(f"{self.package.name}-{self.name}: apply_var_offset error ck_start < 0")
        # 包含校验本身，比如UDP校验
        if self.ck_start + self.ck_size > self.package.max_size:
            raise RuntimeError(f"{self.package.name}-{self.name}: apply_var_offset error ck_start + ck_size > max_size")


class CCheckSum(CheckSumBase):
    """
    C库校验和封装类
    """

    # 默认校验库（cchecksum.dll）缓存
    _cchecksum = None
    _cchecksum_path = None

    @classmethod
    def _load_dll_candidates(cls, candidates):
        """按候选路径顺序加载DLL，返回(库实例, 实际路径)或(None, None)。"""
        for p in ProcessorBase.dedup_paths(candidates):
            if not p.exists():
                continue
            try:
                return ctypes.CDLL(str(p)), str(p)
            except OSError:
                continue
        return None, None

    @classmethod
    def _ensure_default_lib(cls, xml_path: str = None):
        """懒加载默认 cchecksum.dll（支持PyInstaller onefile）。"""
        if cls._cchecksum is not None:
            return

        dll_name = "cchecksum.dll"
        candidates = ProcessorBase.build_search_candidates(dll_name, xml_path=xml_path)
        lib, path = cls._load_dll_candidates(candidates)
        cls._cchecksum = lib
        cls._cchecksum_path = path

    def _load_custom_lib(self, lib_file_name: str):
        """
        加载自定义校验库：
        - 支持 lib_file="foo" / "foo.dll" / 相对路径 / 绝对路径
        - 相对路径优先在xml目录解析，再兜底到运行目录
        """
        candidates = ProcessorBase.build_search_candidates(lib_file_name, xml_path=self.xml_path, suffix=".dll")
        lib, path = CCheckSum._load_dll_candidates(candidates)
        return lib, path

    def load(self, xml_node):
        super().load(xml_node)

        # 若配置了lib_file则优先使用
        self._ck_lib = None
        self._ck_lib_path = None
        lib_file_name = xml_node.attrib.get("lib_file", None)
        if lib_file_name is not None:
            self._ck_lib, self._ck_lib_path = self._load_custom_lib(lib_file_name)

        # 默认 cchecksum.dll（与lib_file使用同一顺序搜索）作为回落
        CCheckSum._ensure_default_lib(self.xml_path)

        # 加载校验函数名
        self.ck_func = None
        ck_func_name = xml_node.attrib.get("ck_func", None)
        if ck_func_name is None:
            raise RuntimeError(f"{self.package.name}-{self.name}: ck_func is None")
        if self._ck_lib is not None and hasattr(self._ck_lib, ck_func_name):
            self.ck_func = getattr(self._ck_lib, ck_func_name)
        elif CCheckSum._cchecksum is not None and hasattr(CCheckSum._cchecksum, ck_func_name):
            self.ck_func = getattr(CCheckSum._cchecksum, ck_func_name)
        else:
            if self._ck_lib is None and CCheckSum._cchecksum is None:
                cands = [str(p) for p in ProcessorBase.get_search_dirs(self.xml_path)]
                raise RuntimeError(f"{self.package.name}-{self.name}: cchecksum.dll or custom lib_file not found, search_dirs={cands}")
            else:
                raise RuntimeError(f"{self.package.name}-{self.name}: ck_func not found: {ck_func_name}")

        # Ensure 64-bit return value isn't truncated by ctypes default c_int.
        self.ck_func.restype = ctypes.c_uint64
        self.ck_func.argtypes = [ctypes.POINTER(ctypes.c_ubyte), ctypes.c_int]

    def pack(self, data, /, **kwargs) -> bool:
        ck_data = data[self.ck_start : self.ck_start + self.ck_size]
        ret = self.ck_func(ctypes.pointer(ctypes.c_ubyte.from_buffer(ck_data)), len(ck_data))
        ret = ret & ((1 << self.size * 8) - 1)
        data[self.offset : self.offset + self.size] = int(ret).to_bytes(self.size, byteorder=self.byteorder)
        return True


class CrcSum(CheckSumBase):
    """通用CRC校验和, 依赖libscrc库
    通过crc_type属性指定CRC类型, 默认ccitt_false
    """

    def load(self, xml_node):
        super().load(xml_node)

        self.crc_type = xml_node.attrib.get("crc_type", "ccitt_false")
        if not hasattr(libscrc, self.crc_type):
            raise RuntimeError(f"{self.package.name}-{self.name}: crc_type not support: {self.crc_type}")
        self.crc_func = getattr(libscrc, self.crc_type)

    def pack(self, data, /, **kwargs) -> bool:
        crc_val = self.crc_func(data[self.ck_start : self.ck_start + self.ck_size])
        ret = crc_val & ((1 << self.size * 8) - 1)
        data[self.offset : self.offset + self.size] = int(ret).to_bytes(self.size, byteorder=self.byteorder)
        return True
