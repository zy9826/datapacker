from backend.processor.ProcessorBase import ProcessorBase, FileGenerator
from backend.processor.CheckSum import *
from pathlib import Path
from abc import abstractmethod


import os
import sys
import random
import importlib


class FillValue(ProcessorBase):
    """填充值类型"""

    def __init__(self):
        super().__init__()
        self.fixed = True
        self.value = 0
        self.bit_mask = 0  # 防止数据溢出
        self.mask = None
        self.mask_lshift = 0
        self.byteorder = "big"  # 默认大端字节序

    def load(self, xml_node):
        super().load(xml_node)
        if self.size > 8:
            raise RuntimeError(f"{self.package.name}-{self.name}: FillValue size too big (more than 8)")
        self.bit_mask = (1 << (self.size * 8)) - 1

        if "byteorder" in xml_node.attrib:
            self.byteorder = xml_node.attrib["byteorder"]
            if self.byteorder not in ["big", "little"]:
                raise RuntimeError(f"{self.package.name}-{self.name}: byteorder must be big or little")

        if "mask" in xml_node.attrib:
            self.mask = int(xml_node.attrib["mask"], 0)
            if self.mask > self.bit_mask or self.mask <= 0:
                raise RuntimeError(f"{self.package.name}-{self.name}: mask error {self.mask}")

            self.mask_lshift = 0
            for i in range(0, 8 * self.size):
                if ((self.mask >> i) & 1) == 1:
                    self.mask_lshift = i
                    break

        if not self.input(xml_node):
            self.value = int(xml_node.attrib.get("value", "0"), 0)

        self.value &= self.bit_mask  # 防止数据溢出
        if self.mask is not None:
            self.value = (self.value << self.mask_lshift) & self.mask

    def pack(self, data, /, **kwargs) -> bool:
        if self.mask is None:
            self.value &= self.bit_mask  # 防止数据溢出
            data[self.offset : self.offset + self.size] = int(self.value).to_bytes(self.size, byteorder=self.byteorder)
        else:
            self.value = (self.value << self.mask_lshift) & self.mask
            origin = int.from_bytes(data[self.offset : self.offset + self.size], byteorder=self.byteorder)
            origin &= ~self.mask  # 清除已有值
            data[self.offset : self.offset + self.size] = (origin | self.value).to_bytes(self.size, byteorder=self.byteorder)
        return True

    def input(self, xml_node):
        input_text = self._get_input(xml_node)
        if input_text is None:
            return False

        try:
            self.value = int(input_text, 0)
        except Exception as e:
            raise RuntimeError(f"{self.package.name}-{self.name}: invalid input {input_text}: {e}")

        if self.input_type == "combo_box":
            if not 0 <= self.value < len(self.opt_value):
                raise RuntimeError(f"{self.package.name}-{self.name}: combo_box index error {input_text}")
            self.value = self.opt_value[self.value]

        return True


class FillPyEval(ProcessorBase):
    """使用py_eval模块计算填充"""

    py_module = None
    py_eval = None

    def __init__(self):
        super().__init__()
        self.value = None
        self.bit_mask = 0  # 防止数据溢出
        self.mask = None
        self.mask_lshift = 0
        self.byteorder = "big"  # 默认大端字节序

    def load(self, xml_node):
        super().load(xml_node)
        if not self.input(xml_node):
            self.value = int(xml_node.attrib.get("value", "0"), 0)

        self.bit_mask = (1 << (self.size * 8)) - 1
        self.byteorder = xml_node.attrib.get("byteorder", "big")
        if self.byteorder not in ["big", "little"]:
            raise RuntimeError(f"{self.package.name}-{self.name}: byteorder must be big or little")

        if "mask" in xml_node.attrib:
            self.mask = int(xml_node.attrib["mask"], 0)
            if self.mask > self.bit_mask or self.mask <= 0:
                raise RuntimeError(f"{self.package.name}-{self.name}: mask error {self.mask}")

            self.mask_lshift = 0
            for i in range(0, 8 * self.size):
                if ((self.mask >> i) & 1) == 1:
                    self.mask_lshift = i
                    break

        # 加载py_eval模块
        if FillPyEval.py_module is None or FillPyEval.py_eval is None:
            sys.path.append(str(self.xml_path))
            FillPyEval.py_module = __import__("py_eval")
            FillPyEval.py_eval = getattr(FillPyEval.py_module, "pyStr2Bytes")

        self.eval_str = xml_node.attrib.get("eval", None)
        if not self.eval_str:
            raise RuntimeError("eval is empty")
        if FillPyEval.py_module is None or FillPyEval.py_eval is None:
            raise RuntimeError("py_eval module invalid")

        try:  # 预编译脚本代码
            self.compiled_code = compile(self.eval_str, "<string>", "eval")
        except SyntaxError as e:
            raise RuntimeError(f"{self.package.name}-{self.name}: eval expression syntax error: {e}")

    def pack(self, data, /, **kwargs) -> bool:
        super().pack(data, **kwargs)
        try:
            if self.value is not None:
                self.package.local_vars["val"] = self.value  # 设置输入参数或默认值
            ret = FillPyEval.py_eval(self.compiled_code, self.package.global_vars, self.package.local_vars)
        except Exception as e:
            raise RuntimeError(f"{self.package.name}-{self.name}: {str(e)}")

        if isinstance(ret, int):
            if self.mask is None:
                val = ret & self.bit_mask
                data[self.offset : self.offset + self.size] = int(val).to_bytes(self.size, byteorder=self.byteorder)
            else:
                val = (ret << self.mask_lshift) & self.mask
                origin = int.from_bytes(data[self.offset : self.offset + self.size], byteorder=self.byteorder)
                origin &= ~self.mask  # 清除已有值
                data[self.offset : self.offset + self.size] = int(origin | val).to_bytes(self.size, byteorder=self.byteorder)
        elif isinstance(ret, bytearray) or isinstance(ret, bytes):
            if len(ret) != self.size:
                raise RuntimeError(f"{self.package.name}-{self.name}: py_eval return size error, current size is {len(ret)}, expected size is {self.size}")
            data[self.offset : self.offset + self.size] = ret
        else:
            raise RuntimeError(f"{self.package.name}-{self.name}: py_eval return type must be bytearray, bytes, int, current type is {type(ret).__name__}")

        return True

    def input(self, xml_node):
        input_text = self._get_input(xml_node)
        if input_text is None:
            return False

        try:
            self.value = input_text
        except Exception as e:
            raise RuntimeError(f"{self.package.name}-{self.name}: invalid input {input_text}: {e}")

        if self.input_type == "combo_box":
            if not 0 <= self.value < len(self.opt_value):
                raise RuntimeError(f"{self.package.name}-{self.name}: combo_box index error {input_text}")
            self.value = self.opt_value[self.value]

        return True


class ExecScript(ProcessorBase):
    """执行脚本"""

    def __init__(self):
        super().__init__()
        self.vfield = True
        self.script_file = ""
        self.script_code = ""
        self.compiled_code = None  # 存储编译后的代码

    def load(self, xml_node):
        super().load(xml_node)
        self.script_code = None
        if "script_file" in xml_node.attrib:
            self.script_file = Path(self.xml_path) / xml_node.attrib["script_file"]
            if not self.script_file.exists():
                raise RuntimeError(f"{self.package.name}-{self.name}: script_file not found")

            with open(self.script_file, "rt", encoding="utf-8") as f:
                self.script_code = f.read()

            if len(self.script_code) <= 0:
                raise RuntimeError(f"{self.package.name}-{self.name}: script_code is empty")

        elif "script_line" in xml_node.attrib:
            self.script_code = xml_node.attrib["script_line"]
            if len(self.script_code) <= 0:
                self.script_code = xml_node.text
            if len(self.script_code) <= 0:
                raise RuntimeError(f"{self.package.name}-{self.name}: script_line is empty")
        else:
            raise RuntimeError(f"{self.package.name}-{self.name}: script_file or script_line attribute missing")

        try:  # 预编译脚本代码
            self.compiled_code = compile(self.script_code, self.name, "exec")  # 使用实际文件名便于调试
        except SyntaxError as e:
            raise RuntimeError(f"{self.package.name}-{self.name}: Script syntax error in {self.script_file}: {e}")

    def pack(self, data, /, **kwargs) -> bool:
        super().pack(data, **kwargs)

        try:
            exec(self.compiled_code, self.package.global_vars, self.package.local_vars)
        except Exception as e:
            raise RuntimeError(f"{self.package.name}-{self.name}: Script execution error in {self.script_file}: {e}")

        return True


class DefineVariable(ProcessorBase):
    """定义变量, 只支持integer类型"""

    def __init__(self):
        super().__init__()
        self.vfield = True
        self.fixed = True

    def load(self, xml_node):
        super().load(xml_node)

        self.var_name = xml_node.attrib["var_name"]
        if self.var_name in self.package.local_vars:
            raise RuntimeError(f"{self.package.name}-{self.name}: variable {self.var_name} already defined")

        if not self.input(xml_node):
            self.value = int(xml_node.attrib.get("value", "0"), 0)  # 默认值0
        self.package.local_vars[self.var_name] = self.value

    def pack(self, data, /, **kwargs) -> bool:
        return True

    def input(self, xml_node):
        input_text = self._get_input(xml_node)
        if input_text is None:
            return False

        try:
            self.value = int(input_text, 0)
        except Exception as e:
            raise RuntimeError(f"{self.package.name}-{self.name}: invalid input {input_text}: {e}")

        if self.input_type == "combo_box":
            if not 0 <= self.value < len(self.opt_value):
                raise RuntimeError(f"{self.package.name}-{self.name}: combo_box index error {input_text}")
            self.value = self.opt_value[self.value]

        return True


class FillVariable(ProcessorBase):
    """填充变量类型"""

    def __init__(self):
        super().__init__()
        self.var_name = ""
        self.byteorder = "big"
        self.bit_mask = 0
        self.mask = None
        self.mask_lshift = 0

    def load(self, xml_node):
        super().load(xml_node)
        if "var_name" not in xml_node.attrib:
            raise RuntimeError(f"{self.package.name}-{self.name}: no var_name attribute")
        self.var_name = xml_node.attrib["var_name"]
        self.byteorder = xml_node.attrib.get("byteorder", "big")
        if self.byteorder not in ["big", "little"]:
            raise RuntimeError(f"{self.package.name}-{self.name}: byteorder must be big or little")
        self.bit_mask = (1 << (self.size * 8)) - 1
        if "mask" in xml_node.attrib:
            self.mask = int(xml_node.attrib["mask"], 0)
            if self.mask > self.bit_mask or self.mask <= 0:
                raise RuntimeError(f"{self.package.name}-{self.name}: mask error {self.mask}")

            self.mask_lshift = 0
            for i in range(0, 8 * self.size):
                if ((self.mask >> i) & 1) == 1:
                    self.mask_lshift = i
                    break

    def pack(self, data, /, **kwargs) -> bool:
        var_value = self.package.local_vars.get(self.var_name, self.package.global_vars.get(self.var_name))
        if var_value is None:
            raise RuntimeError(f"{self.package.name}-{self.name}: variable {self.var_name} is None")

        if self.mask is not None:
            var_value = (var_value << self.mask_lshift) & self.mask
            origin = int.from_bytes(data[self.offset : self.offset + self.size], byteorder=self.byteorder)
            origin &= ~self.mask  # 清除已有值
            data[self.offset : self.offset + self.size] = (origin | var_value).to_bytes(self.size, byteorder=self.byteorder)
        else:
            var_value &= self.bit_mask
            data[self.offset : self.offset + self.size] = int(var_value).to_bytes(self.size, byteorder=self.byteorder)
        return True


class FillArray(ProcessorBase):
    """填充值类型"""

    def __init__(self):
        super().__init__()
        self.fixed = True
        self.value = bytearray()

    def load(self, xml_node):
        super().load(xml_node)

        if not self.input(xml_node):
            text = xml_node.get("value", "")
            try:
                self.value = bytearray.fromhex(text)
            except Exception as e:
                raise RuntimeError(f"{self.package.name}-{self.name}: invalid input {text}: {e}")

        if len(self.value) <= 0:
            raise RuntimeError(f"{self.package.name}-{self.name}: value is empty")

    def pack(self, data, /, **kwargs) -> bool:
        dlen = len(self.value)
        sz = dlen if dlen < self.size else self.size
        data[self.offset : self.offset + sz] = self.value[0:sz]
        return True

    def input(self, xml_node):
        input_text = self._get_input(xml_node)
        if input_text is None:
            return False

        try:
            self.value = bytearray.fromhex(input_text)
        except Exception as e:
            raise RuntimeError(f"{self.package.name}-{self.name}: invalid input {input_text}: {e}")

        return True


class FillFile(ProcessorBase):
    """填充文件数据"""

    def __init__(self):
        super().__init__()
        self._max_pkg = 0
        self.fill_with = 0
        self.filename = ""

        # 生成器相关, 可自定义。可对原始数据预处理
        self.generator = FileGenerator  # 默认生成器
        self.gen_ins = None
        self.gen_iter = None

    def __del__(self):
        if self.gen_ins is not None:
            del self.gen_ins

    def load(self, xml_node):
        self.priority = 99  # 数据源默认优先级最高
        super().load(xml_node)

        self.fill_with = int(xml_node.attrib.get("fill_with", "0"), 0)

        if not self.input(xml_node):
            self.filename = Path(xml_node.attrib.get("filename", ""))

        if not self.filename.exists():
            raise RuntimeError(f"{self.package.name}-{self.name}: file {self.filename} not found")

        # 加载自定义生成器
        gen_str = xml_node.attrib.get("generator", None)
        if gen_str is not None:
            plist = gen_str.split(":")
            if len(plist) == 2:
                sys.path.append(str(self.xml_path))
                try:
                    module = importlib.import_module(plist[0])
                    if hasattr(module, plist[1]):
                        self.generator = getattr(module, plist[1])
                    else:
                        raise RuntimeError(f"{self.package.name}-{self.name}: generator {plist[1]} not found")
                except Exception as e:
                    raise RuntimeError(f"{self.package.name}-{self.name}: generator module '{plist[0]}' import error: {e}")
            else:
                raise RuntimeError(f"{self.package.name}-{self.name}: generator params error: {gen_str}")

        if not self._load_generator():
            raise RuntimeError(f"{self.package.name}-{self.name}: load generator failed; filename: {self.filename}")

    def pack(self, data, /, **kwargs) -> bool:
        buf = next(self.gen_iter, None)
        if buf is None:
            return False

        rlen = len(buf)
        data[self.offset : self.offset + rlen] = buf
        if rlen < self.size:
            for i in range(self.offset + rlen, self.offset + self.size):
                data[i] = self.fill_with
        self.package.local_vars["_dat_len"] = rlen
        return True

    def input(self, xml_node):
        input_text = self._get_input(xml_node)
        if input_text is None:
            return False

        # 输入文件名不能包含空格
        if " " in input_text:
            raise RuntimeError(f"{self.package.name}-{self.name}: file name cannot contain spaces: {input_text}")
        self.filename = Path(input_text)

        return True

    def _load_generator(self) -> bool:
        # 相对路径 查找文件
        if not self.filename.is_absolute():
            p = self.xml_path / self.filename
            if p.exists():
                self.filename = p
            else:
                p = Path.cwd() / self.filename
                if p.exists():
                    self.filename = p
                else:
                    return False

        if not os.path.exists(self.filename) or not os.path.isfile(self.filename):
            return False

        self.gen_ins = self.generator(self.filename, self.size)
        self.gen_iter = iter(self.gen_ins)
        self._max_pkg = self.gen_ins.max_pkg
        return True


class FillPackage(ProcessorBase):
    """填充文件数据"""

    def __init__(self):
        super().__init__()
        self.caller = False  # 是否主动调用 默认False
        self._max_pkg = 0

    def load(self, xml_node):
        self.priority = 99  # 数据源默认优先级最高
        super().load(xml_node)
        self.caller = bool(xml_node.attrib.get("caller", False))

        # 查找数据源包源
        self.pkg_name = xml_node.attrib["pkg_name"]
        self.src_pkg = None

        for pkg in self.package.package_list:
            if pkg.name == self.pkg_name:
                self.src_pkg = pkg
                break

        if self.src_pkg is None:
            raise RuntimeError(f"{self.package.name}-{self.name}: package {self.pkg_name} not found")

        self.eval_str = xml_node.attrib.get("eval", None)
        if self.eval_str:
            if "_max_pkg" in self.eval_str:
                self._max_pkg = eval(self.eval_str, {"__builtins__": None}, {"_max_pkg": self.src_pkg._max_pkg})
            else:
                raise RuntimeError(f"{self.package.name}-{self.name}: eval expression must contain _max_pkg")
        else:
            # 做数据源时设置最大包数
            if not self.fixed:
                self._max_pkg = self.src_pkg._max_pkg

    def pack(self, data, /, **kwargs) -> bool:
        if self.caller:
            if not self.src_pkg.pack():  # 主动调用数据源包的pack方法
                return False

        src_len = len(self.src_pkg.pkg_data)
        wlen = src_len if src_len < self.size else self.size
        data[self.offset : self.offset + wlen] = self.src_pkg.pkg_data[0:wlen]
        self.package.local_vars["_dat_len"] = wlen  # 更新数据长度
        return True


class FillSequenceBase(ProcessorBase):
    def __init__(self):
        super().__init__()  # 调用父类构造函数
        self.max_pkg = 0  # 序列最大包数

    def load(self, xml_node):
        self.priority = 99  # 数据源默认优先级最高
        super().load(xml_node)

        # 非数据源直接return, 不用加载max_pkg
        if self.fixed:
            return

        if not self.input(xml_node):
            self.max_pkg = int(xml_node.attrib["max_pkg"], 0)

        if self.max_pkg <= 0:
            raise RuntimeError(f"{self.package.name}-{self.name}: max_pkg({self.max_pkg}) <= 0 ")

        self._max_pkg = self.max_pkg

    @abstractmethod
    def pack(self, data, /, **kwargs) -> bool:
        pass

    def input(self, xml_node):
        input_text = self._get_input(xml_node, "帧数")
        if input_text is None:
            return False

        self.max_pkg = int(input_text, 0)
        return True


class FillSeqFixedValue(FillSequenceBase):
    def __init__(self):
        super().__init__()
        self.fixed_value = 0

    def load(self, xml_node):
        super().load(xml_node)

        if not self.input2(xml_node):
            self.fixed_value = int(xml_node.attrib.get("fixed_value", "0"), 0)

    def pack(self, data, /, **kwargs):
        for i in range(self.offset, self.offset + self.size):
            data[i] = self.fixed_value
        return True

    def input2(self, xml_node):
        input_text = self._get_input(xml_node, "固定值")
        if input_text is None:
            return False

        try:
            self.fixed_value = int(input_text, 0)
        except Exception as e:
            raise RuntimeError(f"{self.package.name}-{self.name}: invalid input {input_text}: {e}")

        return True


class FillSeqInc8bit(FillSequenceBase):
    def pack(self, data, /, **kwargs) -> bool:
        val = 0
        for i in range(self.offset, self.offset + self.size):
            data[i] = val & 0xFF
            val += 1
        return True


class FillSeqInc16bit(FillSequenceBase):
    def pack(self, data, /, **kwargs) -> bool:
        val = 0
        for i in range(self.offset, self.offset + self.size - 1, 2):
            data[i : i + 2] = (val & 0xFFFF).to_bytes(2, byteorder="big")
            val += 1
        return True


class FillSeqFrmInc8bit(FillSequenceBase):
    def pack(self, data, /, **kwargs) -> bool:
        ba1 = (self.package._cur_pkg & 0xFF).to_bytes(1, byteorder="big")
        data[self.offset : self.offset + self.size] = ba1 * self.size
        return True


class FillSeqRandom8bit(FillSequenceBase):
    def pack(self, data, /, **kwargs) -> bool:
        for i in range(self.offset, self.offset + self.size):
            data[i] = random.randint(0, 0xFF)
        return True
