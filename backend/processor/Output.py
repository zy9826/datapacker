from backend.processor.ProcessorBase import ProcessorBase
from pathlib import Path
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
        self.slice = slice(None, None)  # 默认不切片

    def __del__(self):
        if self.fd is not None:
            self.fd.close()

    def load(self, xml_node):
        # 存储节点的offset和size作为slice使用, 默认值为None
        self.offset = None
        self.size = None
        # 未配置保存节点使用默认节点时xml_node参数是None
        if xml_node is None:
            self.filename = self.package.name
        else:
            super().load(xml_node)
            self.name = xml_node.attrib.get("name", self.name)
            self.filename = xml_node.attrib.get("filename", self.filename)
            self.prefix = xml_node.attrib.get("prefix", self.prefix)
            self.suffix = xml_node.attrib.get("suffix", self.suffix)

            # 加载输入参数
            self._load_input_config(xml_node)

        # 初始化slice
        if self.offset is None or self.size is None:
            self.slice = slice(self.offset, self.size)
        else:
            self.slice = slice(self.offset, self.offset + self.size)

            # 打开文件
        if self.filename == "":
            self.filename = self.name
        if self.filename == "":
            self.filename = self.package.name
        self.filename = self.package.global_save_path / (self.prefix + self.filename + self.suffix)
        self.fd = open(Path(self.filename), self.mode)
        if self.fd is None:
            raise RuntimeError(f"{self.package.name}-{self.name}: open save file error {self.filename}")

    def apply_var_offset(self, var_len: int, var_offset: int, var_size: int):
        if self.offset is None or self.size is None:
            return
        if self.offset + self.size <= var_offset:
            # 在变长字段前面，不变
            return
        elif self.offset >= var_offset + var_size:
            # 在变长字段后面，整体后移
            self.offset += var_len
        else:
            # 包含变长字段，size增加，offset不变
            self.size += var_len

        self.slice = slice(self.offset, self.offset + self.size)


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
            self.fd.write(data[self.slice])
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
                self.fd.write(data[self.slice].hex(self.sep))
            else:
                self.fd.write(data[self.slice].hex())
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
            fd.write(data[self.slice])
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
                fd.write(data[self.slice].hex(self.sep))
            else:
                fd.write(data[self.slice].hex())
            fd.write("\n")
        return True
