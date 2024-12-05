from backend.processor.ProcessorBase import ProcessorBase
import sys

import mmap
from multiprocessing import shared_memory


class DefaultSaveNode(ProcessorBase):
    """默认保存节点"""

    def __init__(self):
        super().__init__()
        self.prefix = ""
        self.suffix = ".dat"
        self.filename = ""
        self.fd = None

    def __del__(self):
        if self.fd is not None:
            self.fd.close()

    def load(self, xml_node):
        if xml_node is not None:
            self.prefix = xml_node.attrib.get("prefix", "")
            self.suffix = xml_node.attrib.get("suffix", ".dat")

        self.filename = self.package.global_save_path / (self.prefix + self.package.name + self.suffix)
        print(self.filename)
        self.fd = open(self.filename, "wb")
        if self.fd is None:
            raise RuntimeError(f"{self.package.name}-{self.name}: open save file error {self.filename}")

    def pack(self, data, /, **kwargs) -> bool:
        if self.fd is not None:
            self.fd.write(data)
        return True


class SharedMemory(ProcessorBase):
    """共享内存保存节点"""

    def __init__(self):
        super().__init__()
        self.shm = None

    def load(self, xml_node):
        shm_name = xml_node.attrib.get("shm_name", "")
        if shm_name == "":
            raise RuntimeError(f"{self.package.name}-{self.name}: shm_name is empty")
        self.shm = shared_memory.SharedMemory(name=shm_name)

    def pack(self, data, /, **kwargs) -> bool:
        pass
