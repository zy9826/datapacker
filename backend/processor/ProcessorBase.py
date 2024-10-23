from abc import ABCMeta, abstractmethod


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

    @abstractmethod
    def load(self, xml_node):
        self.name = xml_node.attrib["name"]
        self.offset = int(xml_node.attrib["offset"], 0)
        self.size = int(xml_node.attrib["size"], 0)

        # fixed
        if "fixed" in xml_node.attrib:
            self.fixed = len(xml_node.attrib["fixed"]) != 0
        else:
            self.fixed = False

        if "priority" in xml_node.attrib:
            self.priority = int(xml_node.attrib["priority"], 0)
        else:
            self.priority = 0

    @abstractmethod
    def pack(self, data, /, **kwargs) -> bool:
        pass
