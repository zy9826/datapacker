from processor.ProcessorBase import ProcessorBase


class XorSum(ProcessorBase):
    def __init__(self):
        super().__init__()

    def load(self, xml_node):
        pass

    def pack(self, data, /, **kwargs) -> bool:
        hb = 0
        lb = 0
        for i in range(0, len(data) - 2, 2):
            hb = hb ^ data[i]
            lb = lb ^ data[i + 1]
        if len(data) % 2 == 1:
            hb = hb ^ data[-3]
        data[-2] = hb & 0xFF
        data[-1] = lb & 0xFF
        return True


class Add8bSum(ProcessorBase):
    """8bit累加和, 返回结果为self.size个字节"""

    def __init__(self):
        super().__init__()

    def load(self, xml_node):
        if self.size <= 0 or self.size > 8:
            raise RuntimeError("size error")

    def pack(self, data, /, **kwargs) -> bool:
        sum = 0
        for i in range(0, len(data) - self.size):
            sum = sum + data[i]

        mask = (1 << self.size * 8) - 1
        val = sum & mask
        data[len(data) - self.size : len(data)] = int(val).to_bytes(self.size, byteorder="big")
        return True


class Add16bSum(ProcessorBase):
    def __init__(self):
        super().__init__()

    def load(self, xml_node):
        if self.size <= 0 or self.size > 8:
            raise RuntimeError("size error")

    def pack(self, data, /, **kwargs) -> bool:
        sum = 0
        for i in range(0, len(data) - self.size, 2):
            sum += int.from_bytes(data[i : i + 2], byteorder="big")

        mask = (1 << self.size * 8) - 1
        val = sum & mask
        data[len(data) - self.size : len(data)] = int(val).to_bytes(self.size, byteorder="big")
        return True


class IsoSum(ProcessorBase):
    def __init__(self):
        super().__init__()

    def load(self, xml_node):
        pass

    def pack(self, data, /, **kwargs) -> bool:
        c0 = 0
        c1 = 0
        for i in range(0, len(data) - 2):
            c0 = c = +data[i]
            c1 = c1 + (len(data) - i) * data[i]

        c0 = c0 % 0xFF
        c1 = c1 % 0xFF

        temp = (c0 + c1) % 0xFF
        temp = 0xFF - temp
        if temp == 0:
            temp = 0xFF
        if c1 == 0:
            c1 = 0xFF
        data[-2] = temp
        data[-1] = c1
        return True
