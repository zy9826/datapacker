from backend.processor.ProcessorBase import ProcessorBase
from pathlib import Path

import libscrc
import ctypes
import os


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

    # 加载全局校验库, 默认和exe同级目录
    _cchecksum = None
    _file = Path(os.getcwd() + "/cchecksum.dll")
    if _file.exists():
        _cchecksum = ctypes.CDLL(str(_file.absolute()))

    # 屏蔽此处抛异常，否则会导致其他文件import CheckSum时就出错
    # else:
    #     raise RuntimeError("cchecksum.dll load failed")

    def load(self, xml_node):
        super().load(xml_node)

        # 加载自定义校验库, 默认和xml同级目录
        self._ck_lib = None
        lib_file_name = xml_node.attrib.get("lib_file", None)
        if lib_file_name is not None:
            lib_file = os.path.join(self.xml_path, f"{lib_file_name}.dll")
            if os.path.exists(lib_file):
                self._ck_lib = ctypes.CDLL(lib_file)

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
                raise RuntimeError(f"{self.package.name}-{self.name}: cchecksum.dll or custom lib_file not found")
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


class XorSum16b(CheckSumBase):
    """异或校验和, 返回结果为self.size个字节"""

    def pack(self, data, /, **kwargs) -> bool:
        hb = 0
        lb = 0
        for i in range(self.ck_start, self.ck_start + self.ck_size, 2):
            hb = hb ^ data[i]
            lb = lb ^ data[i + 1]
        # 支持奇数字节校验
        if self.ck_size % 2 == 1:
            hb = hb ^ data[self.ck_start + self.ck_size - 1]

        ret = int(hb << 8 | lb)
        data[self.offset : self.offset + self.size] = int(ret).to_bytes(self.size, byteorder=self.byteorder)
        return True


class Add8bSum(CheckSumBase):
    """8bit累加和, 返回结果为self.size个字节"""

    def pack(self, data, /, **kwargs) -> bool:
        sum = 0
        for i in range(self.ck_start, self.ck_start + self.ck_size):
            sum = sum + data[i]

        mask = (1 << self.size * 8) - 1
        val = sum & mask
        data[self.offset : self.offset + self.size] = int(val).to_bytes(self.size, byteorder=self.byteorder)
        return True


class Add16bSum(CheckSumBase):
    """ "16bit累加和, 返回结果为self.size个字节"""

    def pack(self, data, /, **kwargs) -> bool:
        sum = 0
        for i in range(self.ck_start, self.ck_start + self.ck_size, 2):
            sum += int.from_bytes(data[i : i + 2], byteorder="big")

        mask = (1 << self.size * 8) - 1
        val = sum & mask
        data[self.offset : self.offset + self.size] = int(val).to_bytes(self.size, byteorder=self.byteorder)
        return True


class IsoSum(CheckSumBase):
    """ISO校验和"""

    def pack(self, data, /, **kwargs) -> bool:
        c0 = 0
        c1 = 0
        for i in range(self.ck_start, self.ck_start + self.ck_size):
            c0 = c0 + data[i]
            c1 = c1 + (self.ck_size - i) * data[i]

        c0 = c0 % 0xFF
        c1 = c1 % 0xFF

        temp = (c0 + c1) % 0xFF
        temp = 0xFF - temp
        if temp == 0:
            temp = 0xFF
        if c1 == 0:
            c1 = 0xFF

        ret = (c1 & 0xFF) | ((temp & 0xFF) << 8)
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
