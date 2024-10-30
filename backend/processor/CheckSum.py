from backend.processor.ProcessorBase import ProcessorBase


class CheckSumBase(ProcessorBase):
    """校验和基类"""

    def __init__(self):
        super().__init__()
        self.ck_start = 0
        self.ck_size = 0

    def load(self, xml_node):
        super().load(xml_node)
        if self.priority == 0:
            self.priority = -1

        self.ck_start = int(xml_node.attrib["ck_start"], 0)
        self.ck_size = int(xml_node.attrib["ck_size"], 0)

        if self.size <= 0 or self.size > 8:
            raise RuntimeError(f"{self.package.name}-{self.name}: return size error")
        if self.ck_size == 0:
            raise RuntimeError(f"{self.package.name}-{self.name} error: ck_size == 0")
        if (self.ck_start + self.ck_size + self.size) > self.package.max_size:
            raise RuntimeError(f"{self.package.name}-{self.name} error: ck_start + ck_size > max_size")


class XorSum16b(CheckSumBase):
    """异或校验和, 返回结果为self.size个字节"""

    def __init__(self):
        super().__init__()

    def load(self, xml_node):
        super().load(xml_node)

    def pack(self, data, /, **kwargs) -> bool:
        hb = 0
        lb = 0
        for i in range(self.ck_start, self.ck_start + self.ck_size, 2):
            hb = hb ^ data[i]
            lb = lb ^ data[i + 1]
        if len(data) % 2 == 1:
            hb = hb ^ data[-3]
        data[self.offset] = hb & 0xFF
        data[self.offset + 1] = lb & 0xFF
        return True


class Add8bSum(CheckSumBase):
    """8bit累加和, 返回结果为self.size个字节"""

    def __init__(self):
        super().__init__()

    def load(self, xml_node):
        super().load(xml_node)

    def pack(self, data, /, **kwargs) -> bool:
        sum = 0
        for i in range(self.ck_start, self.ck_start + self.ck_size):
            sum = sum + data[i]

        mask = (1 << self.size * 8) - 1
        val = sum & mask
        data[self.offset : self.offset + self.size] = int(val).to_bytes(self.size, byteorder="big")
        return True


class Add16bSum(CheckSumBase):
    """ "16bit累加和, 返回结果为self.size个字节"""

    def __init__(self):
        super().__init__()

    def load(self, xml_node):
        super().load(xml_node)

    def pack(self, data, /, **kwargs) -> bool:
        sum = 0
        for i in range(self.ck_start, self.ck_start + self.ck_size, 2):
            sum += int.from_bytes(data[i : i + 2], byteorder="big")

        mask = (1 << self.size * 8) - 1
        val = sum & mask
        data[self.offset : self.offset + self.size] = int(val).to_bytes(self.size, byteorder="big")
        return True


class IsoSum(CheckSumBase):
    """ISO校验和"""

    def __init__(self):
        super().__init__()

    def load(self, xml_node):
        super().load(xml_node)

    def pack(self, data, /, **kwargs) -> bool:
        c0 = 0
        c1 = 0
        for i in range(self.ck_start, self.ck_start + self.ck_size):
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

        data[self.offset] = temp & 0xFF
        data[self.offset + 1] = c1 & 0xFF
        return True


class CrcSum(CheckSumBase):
    """CRC校验和"""

    def __init__(self):
        super().__init__()
        self.crc_table = self.make_crc16_table()

    def load(self, xml_node):
        super().load(xml_node)

    def pack(self, data, /, **kwargs) -> bool:
        ret = 0xFFFF
        for i in range(self.ck_start, self.ck_start + self.ck_size):
            idx = ((ret >> 8) ^ data[i]) & 0xFF
            ret = (ret << 8) ^ self.crc_table[idx]

        data[self.offset : self.offset + self.size] = int(ret).to_bytes(self.size, byteorder="big")
        return True

    def make_crc16_table(self):
        crc_table = []
        reg = 0
        poly = 0x1021
        for i in range(0, 256):
            init = reg ^ ((i << 8) & 0xFFFF)
            for j in range(0, 8):
                if init & 0x8000:
                    init = (init << 1) ^ poly
                else:
                    init <<= 1
            init &= 0xFFFF
            crc_table.append(init)  # 将计算出的CRC值添加到表中
        return crc_table
