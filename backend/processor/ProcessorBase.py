from abc import ABCMeta, ABC, abstractmethod

import os


class ProcessorMeta(ABCMeta):
    """
    处理节点元类
    将类实例字符串存入字典，方便通过字符串构造
    """

    _registry = {}

    def __new__(cls, name, bases, dct):
        new_cls = super().__new__(cls, name, bases, dct)
        ProcessorMeta._registry[name] = new_cls
        return new_cls

    @classmethod
    def create(cls, class_name, *args, **kwargs):
        if class_name in cls._registry:
            return cls._registry[class_name](*args, **kwargs)
        else:
            raise ValueError(f"Class {class_name} not found")


class ProcessorBase(metaclass=ProcessorMeta):
    """
    处理节点基类(抽象类)，定义处理节点接口，元类为ProcessorMeta
    """

    def __init__(self):
        self.package = None  # 所属数据包 DataPackage赋值
        self.xml_path = ""  # 配置文件路径 DataPackage赋值

        # 从xml自行加载
        self.name = ""
        self.offset = 0
        self.size = 0
        self.fixed = False  # 是否固定参数, 默认不固定
        self.priority = 0  # 打包顺序 数字越小优先级越低

        # interactive
        self.input_type = None
        self.input_tips = ""

    @abstractmethod
    def load(self, xml_node):
        self.name = xml_node.attrib.get("name", "")

        # 只有非虚拟字段才需要offset size
        if xml_node.tag != "vField":
            self.offset = int(xml_node.attrib["offset"], 0)
            self.size = int(xml_node.attrib["size"], 0)

        # fixed与priority互斥, fixed=False时priority才有意义
        if "fixed" in xml_node.attrib:
            self.fixed = bool(xml_node.attrib["fixed"])  # fixed
        if "priority" in xml_node.attrib:
            self.priority = int(xml_node.attrib["priority"], 0)  # priority

        # 加载输入参数
        self._load_input_config(xml_node)

    @abstractmethod
    def pack(self, data, /, **kwargs) -> bool:
        pass

    def input(self):
        pass

    def _load_input_config(self, xml_node):
        self.input_type = xml_node.attrib.get("input", None)
        if self.input_type is None:
            return
        self.input_tips = xml_node.attrib.get("input_tips", "")

        if self.input_type not in ["combo_box", "line_edit", "file_input"]:
            raise RuntimeError(f"{self.package.name}-{self.name}: invalid input_type {self.input_type}")

        if self.input_type == "combo_box":
            opt_value = xml_node.attrib.get("opt_value", "")
            opt_text = xml_node.attrib.get("opt_text", "")
            val_list = opt_value.split(";")
            text_list = opt_text.split(";")
            if len(val_list) == 0 or len(val_list) != len(text_list):
                raise RuntimeError(f"{self.package.name}-{self.name}: invalid opt_value or opt_text")

            self.opt_value = []
            for val in val_list:
                try:
                    self.opt_value.append(int(val, 0))
                except Exception as e:
                    raise RuntimeError(f"{self.package.name}-{self.name}: invalid opt_value {val} {e}")
            self.opt_text = text_list

    def _get_input(self):
        if self.input_type == "combo_box":
            for i in range(len(self.opt_value)):

                print(f"{i}: 0x{self.opt_value[i]:X} - {self.opt_text[i]}")
            num = input(f"{self.package.name}-{self.name} {self.input_tips} (0-{len(self.opt_value)-1}): ")
            try:
                num = int(num, 0)
                return self.opt_value[num]
            except Exception as e:
                raise RuntimeError(f"{self.package.name}-{self.name}: invalid input {num}: {e}")
        elif self.input_type == "line_edit":
            from backend.processor.Processor import FillArray, FillValue

            if isinstance(self, FillArray):
                text = input(f"{self.package.name}-{self.name} {self.input_tips}: ")
                try:
                    return bytearray.fromhex(text)
                except Exception as e:
                    raise RuntimeError(f"{self.package.name}-{self.name}: invalid input {text}: {e}")
            else:
                num = input(f"{self.package.name}-{self.name} {self.input_tips}: ")
                try:
                    return int(num, 0)
                except Exception as e:
                    raise RuntimeError(f"{self.package.name}-{self.name}: invalid input {num}: {e}")
        elif self.input_type == "file_input":
            filename = input(f"{self.package.name}-{self.name} {self.input_tips}: ")
            return filename

        return None


class GeneratorBase(ABC):
    """
    数据生成器基类, 抽象类: 用于预处理数据和返回数据
    并非强制要求继承此基类, 但必须实现以下功能：
    1. 实现__iter__方法并返回生成器，返回值是bytearray
    2. 构造函数接受filename和size两个参数
    3. 计算出最大包数max_pkg属性
    4. 上报错误请抛出异常
    """

    def __init__(self, filename: str, size: int):
        self.size = size
        # 内部状态
        self.cur_pkg = 0  # 执行__iter__时更新
        self.max_pkg = 0  # 执行__iter__前计算

        if not os.path.exists(filename) or not os.path.isfile(filename):
            raise RuntimeError(f"file not found: {filename}")

    @abstractmethod
    def __iter__(self):
        pass


class FileGenerator(GeneratorBase):
    """常用文件生成器"""

    def __init__(self, filename: str, size: int):
        super().__init__(filename, size)

        self.ifd = open(filename, "rb")
        if self.ifd is None:
            raise RuntimeError(f"open file {filename} failed")

        file_sz = os.path.getsize(filename)
        if file_sz <= 0:
            raise RuntimeError(f"file {filename} is empty")

        self.max_pkg = (file_sz + self.size - 1) // self.size

    def __iter__(self):
        read_buf = bytearray(self.size)
        while self.cur_pkg < self.max_pkg:
            rsz = self.ifd.readinto(read_buf)
            self.cur_pkg += 1
            yield read_buf
