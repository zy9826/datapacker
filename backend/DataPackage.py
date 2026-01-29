from backend.processor.Processor import *
from backend.processor.Output import *
import importlib.util
from pathlib import Path


class DataPackage:
    """
    DataPackage:执行数据包打包过程和保存功能
    """

    use_default = False  # 使用默认值
    background_mode = False  # background_mode

    package_list = []  # 包格式列表
    global_vars = {"_max_pkg": 0, "_cur_pkg": 0}  # 全局变量表

    def load_script(script_file):
        try:
            module_name = Path(script_file).stem  # 获取模块名（去掉.py后缀）
            spec = importlib.util.spec_from_file_location(module_name, script_file)  # 加载模块
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as e:
            raise RuntimeError(f"Load script failed: {script_file}\nError: {e}")

    def __init__(self):
        self.variable_len_frame = False  # 变长帧标识
        self.not_caller = False  # 是否主动调用
        self.pkg_data = bytearray()  # 包格式数据
        self.xml_path = ""  # 配置文件路径
        self.field_list = []  # 处理节点列表, 不包括固定参数
        self.all_field_list = []  # 所有节点列表, 包括固定参数
        self.save_node_list = []  # 保存节点列表
        self.local_vars = {  # 局部变量表
            "_pkg_data": self.pkg_data,  # 数据数组
            "_dat_len": 0,  # 数据源长度
            "_pkg_len": 0,  # 数据包总长度
        }
        self.global_save_path = ""  # 全局保存路径
        self.fill_with = 0x00  # 填充值

        self._cur_pkg = 0  # 当前包计数
        self._max_pkg = 0  # 最大包计数

    def load(self, xml_node):
        # 加载Package节点
        if xml_node.tag != "Package":
            raise RuntimeError("Invalid xml node: no Package tag")

        # 加载保存标识
        self.save_flag = bool(xml_node.attrib.get("save_flag", False))

        # 加载not_caller标识, 默认为False
        self.not_caller = bool(xml_node.attrib.get("not_caller", False))

        # 加载变长包标识
        self.variable_len_frame = bool(xml_node.attrib.get("var_flag", False))

        # 加载Package->Fields节点
        fields_node = xml_node.find("Fields")
        if fields_node is None:
            raise RuntimeError("Invalid xml node: no Fields tag")

        self.name = fields_node.attrib.get("name", "")
        self.max_size = int(fields_node.attrib["max_size"], 0)
        if self.max_size <= 0:
            raise RuntimeError("Invalid xml node: invalid max_size")
        fill_with = int(fields_node.attrib["fill_with"], 0) & 0xFF
        self.fill_with = fill_with

        # 加载Package->SaveNodes节点
        for node in xml_node.iter("SaveNode"):
            cname = node.attrib.get("class", None)
            if cname is None:
                continue
            p = ProcessorBase.create(cname)
            p.package = self
            p.xml_path = self.xml_path
            p.load(node)
            self.save_node_list.append(p)
        if not self.save_node_list and self.save_flag:
            node = DatSaveNode()
            node.package = self
            node.xml_path = self.xml_path
            node.load(None)
            self.save_node_list.append(node)

        # 加载Field节点
        var_offset = 0
        var_size = 0
        var_len_diff = 0
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

            if self.variable_len_frame:
                p.apply_var_offset(var_len_diff, var_offset, var_size)

                if hasattr(p, "var_len_flag") and p.var_len_diff != 0:
                    var_offset = p.offset
                    var_size = p.size
                    var_len_diff += p.var_len_diff
                    self.max_size += p.var_len_diff
                    for save_node in self.save_node_list:
                        save_node.apply_var_offset(var_len_diff, var_offset, var_size)
                    # print(f"{self.name}-{p.name}: offset={p.offset}, size={p.size}, max_size={self.max_size}")

            # 非虚拟节点检查offset+size是否正确
            if not p.vfield:
                if p.offset < 0:
                    raise RuntimeError(f"{self.name}-{p.name}: offset < 0")
                if p.offset + p.size > self.max_size:
                    raise RuntimeError(f"{self.name}-{p.name}: offset + size > max_size: {p.offset} + {p.size} > {self.max_size}")
            self.all_field_list.append(p)

        # 生成package
        self.pkg_data = bytearray(fill_with.to_bytes(1) * self.max_size)
        self.local_vars["_pkg_data"] = self.pkg_data
        self.local_vars["_pkg_len"] = self.max_size

        # content
        content = fields_node.get("content")
        if content is not None:
            d = bytearray.fromhex(content)
            if len(d) <= self.max_size:
                self.pkg_data[0 : len(d)] = d

        # 执行固定参数pack，分离变化参数
        for p in self.all_field_list:
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
        self._max_pkg = max(max_pkg_list) if len(max_pkg_list) > 0 else 0
        if self._max_pkg <= 0:
            self._max_pkg = 1  # 至少执行一次

        self.local_vars["_max_pkg"] = self._max_pkg
        self.local_vars["_cur_pkg"] = self._cur_pkg

    def pack(self):
        if self._cur_pkg >= self._max_pkg:
            return False

        flag = True
        for f in self.field_list:
            self.local_vars["_pkg_data"] = self.pkg_data  # TODO 是否有必要每次赋值
            flag = f.pack(self.pkg_data)
            if flag is False:
                break
        # 保存数据
        for node in self.save_node_list:
            node.pack(self.pkg_data)
        self._cur_pkg += 1
        self.local_vars["_cur_pkg"] = self._cur_pkg
        return flag
