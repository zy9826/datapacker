from abc import ABCMeta, ABC, abstractmethod
from backend.Console import console

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
    调用顺序: load -> input -> pack
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
        self.vfield = False  # 是否虚拟字段
        self.input_type = None  # 输入方式

    @abstractmethod
    def load(self, xml_node):
        self.name = xml_node.attrib["name"]

        # 只有非虚拟字段才需要offset size
        if not self.vfield:
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

    def input(self, xml_node):
        """
        参数输入方式: 默认交互模式, 先尝试通过input获取, 失败则尝试使用默认值
        参数输入类型: combo_box(输入选项序号)和其他输入类型, 其他所有输入都是字符串, 由子类处理
        """
        return False

    def _load_input_config(self, xml_node):
        self.input_type = xml_node.attrib.get("input", None)
        if not self.input_type:
            return

        if self.input_type == "combo_box":
            opt_value = xml_node.attrib.get("opt_value", "")
            opt_text = xml_node.attrib.get("opt_text", "")
            val_list = opt_value.split(";")
            text_list = opt_text.split(";")
            if len(val_list) != len(text_list):
                raise RuntimeError(f"{self.package.name}-{self.name}: opt_value and opt_text length not equal")
            if len(val_list) == 0 or len(text_list) == 0:
                raise RuntimeError(f"{self.package.name}-{self.name}: opt_value or opt_text is empty")

            self.opt_value = []
            for val in val_list:
                try:
                    self.opt_value.append(int(val, 0))
                except Exception as e:
                    raise RuntimeError(f"{self.package.name}-{self.name}: convert opt_value({val}) to integer failed:  {e}")
            self.opt_text = text_list

    def _get_input(self, xml_node, tips: str = "") -> str:
        if not self.input_type or self.package.use_default:
            return None

        input_text = None
        if self.package.background_mode:
            # background_mode使用配置文件的input_value输入
            input_text = xml_node.attrib.get("input_value", None)
        else:
            if self.input_type == "combo_box":
                console.print(f"{self.package.name}-{self.name}-可选项列表:", style="bold white")
                for i in range(len(self.opt_value)):
                    console.print(f"{i}: 0x{self.opt_value[i]:X} - {self.opt_text[i]}")
                input_text = console.input(f"[bold green]{self.package.name}-{self.name}-选择序号[0-{len(self.opt_value)-1}]: [/bold green]")
            else:
                input_text = console.input(f"[bold green]{self.package.name}-{self.name}{tips}: [/bold green]")
        return input_text


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
            if rsz == self.size:
                yield read_buf
            else:
                yield read_buf[:rsz]
