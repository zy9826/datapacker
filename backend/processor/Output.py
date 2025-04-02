import xml
from backend.processor.ProcessorBase import ProcessorBase, ProcessorMeta
from abc import abstractmethod
import os


class SaveNodeBase(metaclass=ProcessorMeta):
    """
    保存节点基类(抽象类)，定义保存节点接口，元类为ProcessorMeta
    """

    package = None  # 所属数据包 DataPackage赋值
    xml_path = ""  # 配置文件路径 DataPackage赋值

    def __init__(self):
        self.name = ""
        self.prefix = ""
        self.suffix = ".dat"
        self.mode = "wb"  # 默认二进制模式

    def load(self, xml_node):
        # 未配置保存节点使用默认节点是xml_node参数是None
        if xml_node is None:
            self.name = self.package.name
            return

        self.name = xml_node.attrib.get("name", self.package.name)
        self.prefix = xml_node.attrib.get("prefix", "")
        self.suffix = xml_node.attrib.get("suffix", self.suffix)

    @abstractmethod
    def pack(self, data, /, **kwargs) -> bool:
        pass


class DatSaveNode(SaveNodeBase):
    """
    保存为dat文件，默认保存节点
    """

    def __init__(self):
        super().__init__()
        self.suffix = ".dat"
        self.filename = ""
        self.fd = None
        self.mode = "wb"  # 默认二进制模式

    def __del__(self):
        if self.fd is not None:
            self.fd.close()

    def load(self, xml_node):
        super().load(xml_node)
        self.filename = self.package.global_save_path / (self.prefix + self.name + self.suffix)
        self.fd = open(self.filename, self.mode)
        if self.fd is None:
            raise RuntimeError(f"{self.package.name}-{self.name}: open save file error {self.filename}")

    def pack(self, data, /, **kwargs) -> bool:
        if self.fd is not None:
            self.fd.write(data)
        return True


class TxtSaveNode(DatSaveNode):
    """
    保存为txt文件
    """

    def __init__(self):
        super().__init__()
        self.suffix = ".txt"
        self.mode = "wt"

    def pack(self, data, /, **kwargs) -> bool:
        if self.fd is not None:
            self.fd.write(data.hex())
            self.fd.write("\n")
        return True


class SingleDatSaveNode(SaveNodeBase):
    """
    保存为单个dat文件
    """

    def __init__(self):
        super().__init__()
        self.suffix = ".dat"
        self.mode = "wb"  # 默认二进制模式

    def load(self, xml_node):
        super().load(xml_node)

        self.sub_path = self.package.global_save_path / self.name
        os.makedirs(self.sub_path, exist_ok=True)

    def pack(self, data, /, **kwargs) -> bool:
        filename = self.sub_path / (self.prefix + self.name + f"_{self.package._cur_pkg:06}" + self.suffix)
        with open(filename, self.mode) as fd:
            fd.write(data)
        return True


class SingleTxtSaveNode(SingleDatSaveNode):
    """
    保存为单个txt文件
    """

    def __init__(self):
        super().__init__()
        self.suffix = ".txt"
        self.mode = "wt"  # 默认二进制模式

    def pack(self, data, /, **kwargs) -> bool:
        filename = self.sub_path / (self.prefix + self.name + f"_{self.package._cur_pkg:06}" + self.suffix)
        with open(filename, self.mode) as fd:
            fd.write(data.hex())
            fd.write("\n")
        return True
