try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET


from processor.Processor import *


class DataPackage:
    """
    DataPackage:执行数据包打包过程和保存功能
    """

    package_list = []  # 包格式列表
    global_vars = {"_max_pkg": 0, "_cur_pkg": 0}  # 全局变量表

    def __init__(self):
        self.pkg_data = bytearray()
        self.xml_path = ""  # 配置文件路径
        self.field_list = []  # 处理节点列表
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

        # 加载Fields属性 创建bytearray
        self.name = fields_node.attrib["name"]
        if "save_flag" in fields_node.attrib:
            self.save_flag = bool(fields_node.attrib["save_flag"])  # 不为空即为True
        else:
            self.save_flag = False

        if self.save_flag:
            self.save_file = Path(self.global_save_path) / (self.name + ".dat")
            self.ofd = open(self.save_file, "wb")

        self.max_size = int(fields_node.attrib["max_size"], 0)
        if self.max_size <= 0:
            raise RuntimeError("Invalid xml node")
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
            if field_node.tag != "Field":
                raise RuntimeError("Invalid xml node: invalid Field tag")

            # 加载Field
            cname = field_node.attrib["class"]
            p = ProcessorBase.create(cname)
            if p is None:
                raise RuntimeError("Invalid xml node: invalid class name")
            p.package = self
            p.xml_path = self.xml_path
            p.load(field_node)

            # 检查offset+size是否正确
            if p.offset + p.size > self.max_size:
                raise RuntimeError(f"{self.name}-{p.name}: offset + size > max_size")

            # 固定参数只执行一次; 可变参数根据index排序 index越小优先级越低
            if p.fixed:
                p.pack(self.pkg_data)
            else:
                if len(self.field_list) <= 0:
                    self.field_list.append(p)
                else:
                    for idx in range(0, len(self.field_list)):
                        if self.field_list[idx].priority < p.priority:
                            self.field_list.insert(idx, p)
                            break
                    else:
                        self.field_list.append(p)

        # TODO DEL
        # temp_list = [(p.name, p.priority) for p in self.field_list]
        # print(temp_list)

        # 加载变量
        var_nodes = xml_node.findall("Variable")
        if var_nodes is None:
            raise RuntimeError("Invalid xml node")
        for var_node in var_nodes:
            name = var_node.attrib["name"]
            if name in self.local_vars:
                raise RuntimeError("Invalid xml node: repeated name")

            value = var_node.attrib["value"]
            data_type = var_node.attrib["data_type"]
            # 先只考虑int类型
            self.local_vars[name] = int(value, 0)

    def pack(self):
        flag = True
        for f in self.field_list:
            self.local_vars["_pkg_data"] = self.pkg_data
            flag = f.pack(self.pkg_data, global_vars=DataPackage.global_vars, local_vars=self.local_vars)
            if flag is False:
                break

        # 数据保存
        if flag is False:
            return flag
        if self.ofd is not None:
            self.ofd.write(self.pkg_data)
        return flag

    def save(self):
        pass
