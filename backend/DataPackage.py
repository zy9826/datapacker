from backend.processor.Processor import *
import importlib.util


class DataPackage:
    """
    DataPackage:执行数据包打包过程和保存功能
    """

    # 后端模式 通过配置文件的input_value属性输入数据
    backend_mode = False
    # 交互模式 通过控制台输入
    interactive = False
    # 包格式列表
    package_list = []
    # 全局变量表
    global_vars = {"_max_pkg": 0, "_cur_pkg": 0}

    def load_script(script_file):
        try:
            module_name = script_file.split("/")[-1].replace(".py", "")  # 获取模块名（去掉.py后缀）
            spec = importlib.util.spec_from_file_location(module_name, script_file)  # 加载模块
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as e:
            raise RuntimeError(f"Load script failed: {script_file}\nError: {e}")

    def __init__(self):
        self.pkg_data = bytearray()
        self.xml_path = ""  # 配置文件路径
        self.field_list = []  # 处理节点列表, 不包括固定参数
        self.all_field_list = []  # 所有节点列表, 包括固定参数
        self.save_node_list = []  # 保存节点列表
        self.local_vars = {"_pkg_data": self.pkg_data, "_dat_len": 0}  # 变量表 _dat_len:数据源长度
        self.global_save_path = ""  # 全局保存路径

        self._cur_pkg = 0  # 当前包计数
        self._max_pkg = 0  # 最大包计数

    def load(self, xml_node):
        if xml_node.tag != "Package":
            raise RuntimeError("Invalid xml node: no Package tag")

        # 加载保存标识
        self.save_flag = bool(xml_node.attrib.get("save_flag", False))

        # 加载Fields节点
        fields_node = xml_node.find("Fields")
        if fields_node is None:
            raise RuntimeError("Invalid xml node: no Fields tag")

        self.name = fields_node.attrib.get("name", "")
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

        # 加载Field节点
        for field_node in fields_node:
            # 加载Field class 可以为空, 默认使用fill_with填充
            cname = field_node.attrib.get("class", None)
            if cname is None:
                continue
            p = ProcessorBase.create(cname)
            if p is None:
                raise RuntimeError(f"{self.name}-{p.name} invalid class name: {cname}")
            p.package = self
            p.xml_path = self.xml_path
            p.load(field_node)

            # 非虚拟节点检查offset+size是否正确
            if not p.vfield:
                if p.offset < 0 or p.size <= 0:
                    raise RuntimeError(f"{self.name}-{p.name}: offset < 0 or size <= 0")
                if p.offset + p.size > self.max_size:
                    raise RuntimeError(f"{self.name}-{p.name}: offset + size > max_size: {p.offset} + {p.size} > {self.max_size}")

            self.all_field_list.append(p)
            # 交互模式输入参数
            if DataPackage.interactive:
                p.input(field_node)
            # 执行固定参数pack，分离变化参数
            if p.fixed:
                p.pack(self.pkg_data)
            else:
                self.field_list.append(p)

        # 排序变化参数priority
        self.field_list.sort(key=lambda x: x.priority, reverse=True)
        # 比较max_pkg， 所有节点都参与计算，包括固定参数
        max_pkg_list = []
        for f in self.all_field_list:
            if hasattr(f, "_max_pkg"):
                max_pkg_list.append(f._max_pkg)
        self._max_pkg = min(max_pkg_list) if len(max_pkg_list) > 0 else 0
        if self._max_pkg <= 0:
            raise RuntimeError(f"DataPackage {self.name}: max_pkg <= 0 {self._max_pkg}")

        # 加载SaveNode节点
        for node in xml_node.iter("SaveNode"):
            cname = node.attrib.get("class", None)
            if cname is None:
                continue
            p = ProcessorBase.create(cname)
            if p is None:
                raise RuntimeError(f"{self.name}-{p.name} invalid class name: {cname}")
            p.package = self
            p.xml_path = self.xml_path
            p.load(node)
            self.save_node_list.append(p)
        if not self.save_node_list and self.save_flag:
            node = DefaultSaveNode()
            node.package = self
            node.xml_path = self.xml_path
            node.load(None)
            self.save_node_list.append(node)

    def pack(self):
        flag = True
        for f in self.field_list:
            self.local_vars["_pkg_data"] = self.pkg_data
            flag = f.pack(self.pkg_data)
            if flag is False:
                break
        # 保存数据
        for node in self.save_node_list:
            node.pack(self.pkg_data)
        return flag
