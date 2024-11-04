from backend.processor.Processor import *


class DataPackage:
    """
    DataPackage:执行数据包打包过程和保存功能
    """

    package_list = []  # 包格式列表
    global_vars = {"_max_pkg": 0, "_cur_pkg": 0}  # 全局变量表

    def __init__(self):
        self.pkg_data = bytearray()
        self.xml_path = ""  # 配置文件路径
        self.field_list = []  # 处理节点列表, 不包括固定参数
        self.all_field_list = []  # 所有节点列表, 包括固定参数
        self.local_vars = {"_pkg_data": self.pkg_data, "_dat_len": 0}  # 变量表 _dat_len:数据源长度

        self.global_save_path = ""  # 全局保存路径
        self.save_file = ""  # 保存文件名
        self.ofd = None  # 输出文件句柄

    def __del__(self):
        if self.ofd is not None:
            self.ofd.close()

    def load(self, xml_node):
        if xml_node.tag != "Package":
            raise RuntimeError("Invalid xml node: no Package tag")

        fields_node = xml_node.find("Fields")
        if fields_node is None:
            raise RuntimeError("Invalid xml node: no Fields tag")

        self.name = fields_node.attrib.get("name", "")
        self.save_flag = bool(fields_node.attrib.get("save_flag", False))

        if self.save_flag:
            self.save_file = Path(self.global_save_path) / (self.name + ".dat")
            self.ofd = open(self.save_file, "wb")

        self.max_size = int(fields_node.attrib["max_size"], 0)
        if self.max_size <= 0:
            raise RuntimeError("Invalid xml node: invalid max_size")
        fill_with = int(fields_node.attrib["fill_with"], 0) & 0xFF
        self.pkg_data = bytearray(self.max_size)
        # fill_with
        for v in self.pkg_data:
            v = fill_with
        # content
        content = fields_node.get("content")
        if content is not None:
            d = bytearray.fromhex(content)
            if len(d) <= self.max_size:
                self.pkg_data[0 : len(d)] = d

        # 加载Fields子节点
        for field_node in fields_node:
            if field_node.tag != "Field" and field_node.tag != "vField":
                raise RuntimeError("Invalid xml node: invalid Field tag")

            # 加载Field
            # class 可以为空, 默认使用fill_with填充
            cname = field_node.attrib.get("class", None)
            if cname is None:
                continue
            p = ProcessorBase.create(cname)
            if p is None:
                raise RuntimeError(f"{self.name}-{p.name} invalid class name: {cname}")
            p.package = self
            p.xml_path = self.xml_path
            p.load(field_node)

            # 检查offset+size是否正确
            if p.offset < 0 or p.size <= 0:
                raise RuntimeError(f"{self.name}-{p.name}: offset < 0 or size <= 0")
            if p.offset + p.size > self.max_size:
                raise RuntimeError(f"{self.name}-{p.name}: offset + size > max_size: {p.offset} + {p.size} > {self.max_size}")

            self.all_field_list.append(p)

    def pack(self):
        flag = True
        for f in self.field_list:
            self.local_vars["_pkg_data"] = self.pkg_data
            flag = f.pack(self.pkg_data)
            if flag is False:
                break

        # 数据保存
        if flag is False:
            return flag
        if self.ofd is not None:
            self.ofd.write(self.pkg_data)
        return flag

    def input(self):
        for f in self.all_field_list:
            f.input()
