from io import IOBase
from backend.processor.ProcessorBase import ProcessorBase
from backend.processor.CheckSum import *
from pathlib import Path

import os
import sys


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
        self.value = int(xml_node.attrib.get("value", "0"), 0)

    def pack(self, data, /, **kwargs) -> bool:
        data[self.offset : self.offset + self.size] = int(self.value).to_bytes(self.size, byteorder="big")
        return True

    def input(self):
        if self.input_type is None:
            return

        if self.data_type != "integer":
            raise RuntimeError(f"{self.package.name}-{self.name}: FillValue only support integer input")

        ret = self._get_input()
        if isinstance(ret, int):
            self.value = ret
        else:
            raise RuntimeError(f"{self.package.name}-{self.name}: get_input error {ret}")


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
        if not self.eval_str:
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


class ExecScript(ProcessorBase):
    """执行脚本"""

    def __init__(self):
        super().__init__()
        self.script_file = ""
        self.script_code = ""
        self.compiled_code = None  # 存储编译后的代码

    def load(self, xml_node):
        super().load(xml_node)
        if "script_file" not in xml_node.attrib:
            raise RuntimeError(f"{self.package.name}-{self.name}: script_file is empty")

        self.script_file = Path(self.xml_path) / xml_node.attrib["script_file"]
        if not self.script_file.exists():
            raise RuntimeError(f"{self.package.name}-{self.name}: script_file not found")

        with open(self.script_file, "rt", encoding="utf-8") as f:
            self.script_code = f.read()

        if len(self.script_code) <= 0:
            raise RuntimeError(f"{self.package.name}-{self.name}: script_code is empty")

        try:  # 预编译脚本代码
            self.compiled_code = compile(self.script_code, self.script_file, "exec")  # 使用实际文件名便于调试
        except SyntaxError as e:
            raise RuntimeError(f"{self.package.name}-{self.name}: Script syntax error in {self.script_file}: {e}")

    def pack(self, data, /, **kwargs) -> bool:
        super().pack(data, **kwargs)

        global_vars = kwargs.get("global_vars", None)
        local_vars = kwargs.get("local_vars", None)

        try:
            exec(self.compiled_code, global_vars, local_vars)
        except Exception as e:
            raise RuntimeError(f"{self.package.name}-{self.name}: Script execution error in {self.script_file}: {e}")

        return True


class FillVariable(ProcessorBase):
    """填充变量类型"""

    def __init__(self):
        super().__init__()
        self.var_name = ""

    def load(self, xml_node):
        super().load(xml_node)
        if "var_name" not in xml_node.attrib:
            raise RuntimeError(f"{self.package.name}-{self.name}: no var_name attribute")
        self.var_name = xml_node.attrib["var_name"]

    def pack(self, data, /, **kwargs) -> bool:
        global_vars = kwargs.get("global_vars", None)
        local_vars = kwargs.get("local_vars", None)

        var_value = local_vars.get(self.var_name, global_vars.get(self.var_name))
        if var_value is None:
            raise RuntimeError(f"{self.package.name}-{self.name}: variable {self.var_name} is None")

        data[self.offset : self.offset + self.size] = int(var_value).to_bytes(self.size, byteorder="big")
        return True


class FillArray(ProcessorBase):
    """填充值类型"""

    def __init__(self):
        super().__init__()
        self.fixed = True
        self.value = bytearray()

    def load(self, xml_node):
        super().load(xml_node)
        val_attr = xml_node.attrib["value"]
        self.value = bytearray.fromhex(val_attr)
        if len(self.value) <= 0:
            raise RuntimeError(f"{self.package.name}-{self.name}: value is empty")

    def pack(self, data, /, **kwargs) -> bool:
        dlen = len(self.value)
        sz = dlen if dlen < self.size else self.size
        if sz <= 0:
            raise RuntimeError(f"{self.package.name}-{self.name}: bytearray size is 0")
        data[self.offset : self.offset + sz] = self.value[0:sz]
        return True

    def input(self):
        if self.input_type is None:
            return

        if self.input_type != "bin":
            raise RuntimeError(f"{self.package.name}-{self.name}: FillArray only support bin input")

        ret = self.get_input()
        if isinstance(ret, bytearray):
            self.value = ret
        else:
            raise RuntimeError(f"{self.package.name}-{self.name}: get_input error {ret}")


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
            raise RuntimeError(f"{self.package.name}-{self.name}: size error")
        self.buf = bytearray(self.size)  # 申请缓存

        # 由于支持file_input输入, filename可为空, 文件存在性检查放在pack时
        self.filename = Path(xml_node.attrib["filename"])

        try:
            self.fill_with = int(xml_node.attrib["fill_with"])
        except:
            self.fill_with = 0

    def pack(self, data, /, **kwargs) -> bool:
        if self.ifd is None:
            if not self.filename.exists():
                raise RuntimeError(f"{self.package.name}-{self.name}: file not found")
            file_sz = os.path.getsize(self.filename)
            if file_sz <= 0:
                raise RuntimeError(f"{self.package.name}-{self.name}: file size is 0")

            self.ifd = open(self.filename, "rb")
            max_pkg = (file_sz + self.size - 1) // self.size
            from backend.DataPackage import DataPackage

            DataPackage.global_vars["_max_pkg"] = max_pkg

        if self.ifd is None:
            raise RuntimeError(f"{self.package.name}-{self.name}: file descriptor is None")

        rsz = self.ifd.readinto(self.buf)
        if rsz <= 0:
            return False

        if rsz < self.size:
            for i in range(rsz, self.size):
                self.buf[i] = self.fill_with

        data[self.offset : self.offset + self.size] = self.buf
        self.package.local_vars["_dat_len"] = rsz
        return True

    def input(self):
        if self.input_type is None:
            return

        if self.input_type != "file_input":
            raise RuntimeError(f"{self.package.name}-{self.name}: FillFile only support file_input input")

        ret = self.get_input()
        if isinstance(ret, str):
            self.filename = Path(ret)
        else:
            raise RuntimeError(f"{self.package.name}-{self.name}: get_input error {ret}")


class FillPackage(ProcessorBase):
    """填充文件数据"""

    def __init__(self):
        super().__init__()

    def load(self, xml_node):
        super().load(xml_node)
        self.pkg_name = xml_node.attrib["pkg_name"]
        self.src_pkg = None
        from backend.DataPackage import DataPackage

        for pkg in DataPackage.package_list:
            if pkg.name == self.pkg_name:
                self.src_pkg = pkg
                break

        if self.src_pkg is None:
            raise RuntimeError(f"{self.package.name}-{self.name}: package {self.pkg_name} not found")

    def pack(self, data, /, **kwargs) -> bool:
        data[self.offset : self.offset + self.size] = self.src_pkg.pkg_data
        return True
