from backend.processor.Output import SaveNodeBase
from abc import abstractmethod
from backend.Console import console
import xml
import os


class DatSaveWithFillFrm(SaveNodeBase):
    """
    dat填充帧存储节点
    填充帧数通过输入获取
    """

    def __init__(self):
        super().__init__()
        self.fill_cnt = 0
        self.fill_frm = bytearray()

    def pack(self, data, /, **kwargs) -> bool:
        if len(self.fill_frm) != len(data):
            self.fill_frm = bytearray(b"\x00" * len(data))

        if self.fd is not None:
            self.fd.write(data)
            if self.fill_cnt <= 0:
                return True
            for i in range(0, self.fill_cnt):
                self.fd.write(self.fill_frm)
        return True

    def load(self, xml_node):
        super().load(xml_node)

        if "fill_cnt" in xml_node.attrib:
            self.fill_cnt = int(xml_node.attrib["fill_cnt"])
        else:
            self.fill_cnt = int(console.input(f"[bold green]设置填充帧数: [/bold green]"))

        if self.fill_cnt < 0:
            raise RuntimeError(f"DatSaveWithFillFrm: 填充帧数量不能小于0")
