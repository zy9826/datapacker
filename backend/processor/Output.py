import xml
from backend.processor.ProcessorBase import ProcessorBase
from abc import abstractmethod
import os


class SaveNodeBase(ProcessorBase):
    """
    保存节点基类(抽象类)，定义保存节点接口，元类为ProcessorMeta
    """

    def __init__(self):
        super().__init__()

        self.name = ""
        self.filename = ""
        self.prefix = ""
        self.suffix = ".dat"
        self.mode = "wb"  # 默认二进制模式
        self.fd = None

    def __del__(self):
        if self.fd is not None:
            self.fd.close()

    def load(self, xml_node):
        # 未配置保存节点使用默认节点时xml_node参数是None
        if xml_node is None:
            self.filename = self.package.name
        else:
            self.name = xml_node.attrib.get("name", self.name)
            self.filename = xml_node.attrib.get("filename", self.package.name)
            self.prefix = xml_node.attrib.get("prefix", self.prefix)
            self.suffix = xml_node.attrib.get("suffix", self.suffix)

        self.filename = self.package.global_save_path / (self.prefix + self.filename + self.suffix)
        self.fd = open(self.filename, self.mode)
        if self.fd is None:
            raise RuntimeError(f"{self.package.name}-{self.filename}: open save file error {self.filename}")

        # 加载输入参数
        self._load_input_config(xml_node)

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

    def pack(self, data, /, **kwargs) -> bool:
        if self.fd is not None:
            self.fd.write(data)
        return True


class TxtSaveNode(SaveNodeBase):
    """
    保存为txt文件
    """

    def __init__(self):
        super().__init__()
        self.suffix = ".txt"
        self.mode = "wt"

    def __del__(self):
        if self.fd is not None:
            self.fd.close()

    def load(self, xml_node):
        super().load(xml_node)
        self.sep = xml_node.attrib.get("sep", "")  # 分隔符，默认为空

    def pack(self, data, /, **kwargs) -> bool:
        if self.fd is not None:
            if len(self.sep) == 1:
                self.fd.write(data.hex(self.sep))
            else:
                self.fd.write(data.hex())
            self.fd.write("\n")
        return True


class SingleDatSaveNode(DatSaveNode):
    """
    保存为单个dat文件
    """

    def __init__(self):
        super().__init__()
        self.suffix = ".dat"
        self.mode = "wb"  # 默认二进制模式

    def load(self, xml_node):
        super().load(xml_node)

        self.sub_path = xml_node.attrib.get("sub_path", None)
        if self.sub_path is None:
            self.sub_path = self.filename + "_dat"
        self.sub_path = self.package.global_save_path / self.sub_path
        os.makedirs(self.sub_path, exist_ok=True)

    def pack(self, data, /, **kwargs) -> bool:
        filename = self.sub_path / (self.prefix + self.filename + f"_{self.package._cur_pkg:06}" + self.suffix)
        with open(filename, self.mode) as fd:
            fd.write(data)
        return True


class SingleTxtSaveNode(TxtSaveNode):
    """
    保存为单个txt文件
    """

    def __init__(self):
        super().__init__()
        self.suffix = ".txt"
        self.mode = "wt"  # 默认二进制模式

    def load(self, xml_node):
        super().load(xml_node)

        self.sub_path = xml_node.attrib.get("sub_path", None)
        if self.sub_path is None:
            self.sub_path = self.filename + "_txt"
        self.sub_path = self.package.global_save_path / self.sub_path
        os.makedirs(self.sub_path, exist_ok=True)

    def pack(self, data, /, **kwargs) -> bool:
        filename = self.sub_path / (self.prefix + self.filename + f"_{self.package._cur_pkg:06}" + self.suffix)
        with open(filename, self.mode) as fd:
            if len(self.sep) == 1:
                fd.write(data.hex(self.sep))
            else:
                fd.write(data.hex())
            fd.write("\n")
        return True
