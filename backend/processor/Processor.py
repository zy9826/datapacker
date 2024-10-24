from processor.ProcessorBase import ProcessorBase
from processor.CheckSum import *
from pathlib import Path

import os
import sys


try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


class FillValue(ProcessorBase):
    """填充值类型"""

    def __init__(self):
        super().__init__()
        self.fixed = True
        self.value = 0

    def load(self, xml_node):
        super().load(xml_node)
        if self.size > 8:
            raise RuntimeError("FillValue size too big")
        self.value = int(xml_node.attrib["value"], 0)

    def pack(self, data, /, **kwargs) -> bool:
        data[self.offset : self.offset + self.size] = int(self.value).to_bytes(self.size, byteorder="big")
        return True


class FillPyEval(ProcessorBase):
    """使用py_eval模块计算填充"""

    py_module = None
    py_eval = None

    def __init__(self):
        super().__init__()

    def load(self, xml_node):
        super().load(xml_node)

        # 加载py_eval模块
        if FillPyEval.py_module is None or FillPyEval.py_eval is None:
            sys.path.append(str(self.xml_path))
            FillPyEval.py_module = __import__("py_eval")
            FillPyEval.py_eval = getattr(FillPyEval.py_module, "pyStr2Bytes")

        self.eval_str = xml_node.attrib["eval"]
        if self.eval_str == "":
            raise RuntimeError("eval is empty")
        if FillPyEval.py_module is None or FillPyEval.py_eval is None:
            raise RuntimeError("py_eval module invalid")

    def pack(self, data, /, **kwargs) -> bool:
        super().pack(data, **kwargs)
        try:
            ret = FillPyEval.py_eval(self.eval_str, self.package.global_vars, self.package.local_vars)
        except Exception as e:
            raise RuntimeError(f"{self.package.name}-{self.name}: {str(e)}")
        if ret is None:
            raise RuntimeError(f"{self.package.name}-{self.name}: py_eval error")
        if len(ret) != self.size:
            raise RuntimeError("py_eval return size error")

        data[self.offset : self.offset + self.size] = ret
        return True


class FillVariable(ProcessorBase):
    """填充变量类型"""

    def __init__(self):
        super().__init__()
        self.fixed = False
        self.var_name = ""
        self.script_file = ""
        self.script_code = ""

    def load(self, xml_node):
        super().load(xml_node)
        self.var_name = xml_node.attrib["var_name"]

        # var_script属性可以为空
        if "var_script" in xml_node.attrib:
            script_file = Path(self.xml_path) / xml_node.attrib["var_script"]
            # 脚本文件可以为空
            if script_file.exists():
                self.script_file = script_file
                with open(script_file, "rt", encoding="utf-8") as f:
                    for line in f.readlines():
                        self.script_code += line

    def pack(self, data, /, **kwargs) -> bool:
        global_vars = kwargs.get("global_vars", None)
        local_vars = kwargs.get("local_vars", None)

        if self.var_name not in local_vars and self.var_name not in global_vars:
            raise RuntimeError("variable not found")

        if self.var_name in local_vars:
            data[self.offset : self.offset + self.size] = int(local_vars[self.var_name]).to_bytes(self.size, byteorder="big")
        elif self.var_name in global_vars:
            data[self.offset : self.offset + self.size] = int(global_vars[self.var_name]).to_bytes(self.size, byteorder="big")

        if len(self.script_code) > 0:
            exec(self.script_code, global_vars, local_vars)
        return True


class FillArray(ProcessorBase):
    """填充值类型"""

    def __init__(self):
        super().__init__()
        self.fixed = True
        self.value = 0

    def load(self, xml_node):
        super().load(xml_node)
        val_attr = xml_node.attrib["value"]
        if len(val_attr) <= 0:
            raise RuntimeError("value is empty")
        print(val_attr)
        self.value = bytearray.fromhex(val_attr)

    def pack(self, data, /, **kwargs) -> bool:
        dlen = len(self.value)
        sz = dlen if dlen < self.size else self.size
        data[self.offset : self.offset + sz] = self.value[0:sz]
        return True


class FillFile(ProcessorBase):
    """填充文件数据"""

    def __init__(self):
        super().__init__()
        self.fill_with = 0
        self.filename = ""
        self.ifd = None

    def __del__(self):
        if self.ifd is not None:
            self.ifd.close()

    def load(self, xml_node):
        super().load(xml_node)
        if self.size <= 0:
            raise RuntimeError("size error")
        self.buf = bytearray(self.size)  # 申请缓存

        filename = Path(xml_node.attrib["filename"])
        if filename.exists() is False:
            raise RuntimeError(f"{self.package.name}-{self.name}-file not found")
        self.filename = filename
        self.ifd = open(self.filename, "rb")

        try:
            self.fill_with = int(xml_node.attrib["fill_with"])
        except:
            self.fill_with = 0

        max_pkg = (os.path.getsize(self.filename) + self.size - 1) // self.size
        from DataPackage import DataPackage

        DataPackage.global_vars["_max_pkg"] = max_pkg

    def pack(self, data, /, **kwargs) -> bool:
        rsz = self.ifd.readinto(self.buf)
        if rsz <= 0:
            return False

        if rsz < self.size:
            for i in range(rsz, self.size):
                self.buf[i] = self.fill_with

        data[self.offset : self.offset + self.size] = self.buf
        self.package.local_vars["_dat_len"] = rsz
        return True


class FillPackage(ProcessorBase):
    """填充文件数据"""

    def __init__(self):
        super().__init__()

    def load(self, xml_node):
        super().load(xml_node)
        self.pkg_name = xml_node.attrib["pkg_name"]
        self.src_pkg = None
        from DataPackage import DataPackage

        for pkg in DataPackage.package_list:
            if pkg.name == self.pkg_name:
                self.src_pkg = pkg
                break

        if self.src_pkg is None:
            raise RuntimeError("package not found")

    def pack(self, data, /, **kwargs) -> bool:
        data[self.offset : self.offset + self.size] = self.src_pkg.pkg_data
        return True
