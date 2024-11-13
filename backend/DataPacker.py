import xml.etree.cElementTree as ET

from backend.DataPackage import DataPackage
from pathlib import Path
from datetime import datetime

import os
import sys


class DataPacker:
    """数据打包器"""

    interactive = False  # 是否进入交互模式

    def __init__(self):
        super().__init__()
        self._cur_pkg = 0  # 当前包计数
        self._max_pkg = 0  # 最大包计数

    def load(self, xml_path) -> bool:
        xml_filename = Path(xml_path) / "config.xml"
        if not xml_filename.exists():
            raise RuntimeError(f"Config file not found: {xml_filename}")

        tree = ET.parse(xml_filename)
        root = tree.getroot()
        print(f"加载配置: {xml_path}")

        # 加载全局保存路径
        spath = None
        save_node = root.find("GlobalSavePath")
        if save_node is not None:
            spath = Path(save_node.attrib.get("save_path", None))
        else:
            print("GlobalSavePath tag not found in config file")

        if spath is None:
            spath = Path.cwd() / "output"
        if not spath.exists():
            os.makedirs(spath, exist_ok=True)

        config_named = bool(save_node.attrib.get("config_named", False))
        if config_named:
            spath = spath / Path(xml_path).name
            os.makedirs(spath, exist_ok=True)

        time_named = bool(save_node.attrib.get("time_named", False))
        if time_named:
            spath = spath = spath = spath / datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs(spath, exist_ok=True)
        self.global_save_path = Path(spath)

        # 加载脚本
        for script_node in root.iter("LoadScript"):
            filename = script_node.attrib.get("script_file", "")
            if filename == "":
                raise RuntimeError(f"LoadScript Node no script_file attribute is empty!")
            script_file = Path(xml_path) / filename
            flag = DataPackage.load_script(str(script_file))

        # 加载Package配置
        for package_node in root.iter("Package"):
            package = DataPackage()
            package.xml_path = xml_path
            package.global_save_path = self.global_save_path

            package.load(package_node)
            DataPackage.package_list.append(package)

        # 计算最大包计数
        max_pkg_list = [p._max_pkg for p in DataPackage.package_list]
        self._max_pkg = min(max_pkg_list) if len(max_pkg_list) > 0 else 0
        if self._max_pkg <= 0:
            raise RuntimeError(f"DataPacker max_pkg <= 0 {self._max_pkg}")
        DataPackage.global_vars["_max_pkg"] = self._max_pkg
        DataPackage.global_vars["_cur_pkg"] = 0

        pkg_name_list = [p.name for p in DataPackage.package_list]
        print(f"成功加载{len(DataPackage.package_list)}种包格式: {pkg_name_list}")
        return True

    def exec(self):
        # 每个包的每个可变参数依次执行
        flag = True
        while flag and self._cur_pkg < self._max_pkg:
            for package in DataPackage.package_list:
                flag = package.pack()
                if not flag:
                    print("flag exit")
                    break

            self._cur_pkg += 1
            DataPackage.global_vars["_cur_pkg"] = self._cur_pkg
            if self._cur_pkg % 1000 == 0:
                self._update_progress(self._cur_pkg, self._max_pkg)

        self._update_progress(self._cur_pkg, self._max_pkg)
        print("\r")

    def _update_progress(self, num, total):
        rate = num / total
        rate_num = int(rate * 100)
        try:
            terminal_width = os.get_terminal_size().columns  # 获取终端宽度
            bar_length = terminal_width - 22  # 预留显示百分比和数字的空间（约22个字符）
            filled_length = int(bar_length * rate)  # 根据终端宽度调整进度条长度
            empty_length = bar_length - filled_length

            r = f"\r[{'>' * filled_length}{' ' * empty_length}] {rate_num}% {num}/{total}"
            sys.stdout.write(r)
            sys.stdout.flush()
        except OSError:
            # 如果无法获取终端大小（比如在某些IDE中），使用默认长度
            r = f"\r[{'>' * int(rate_num)}{' ' * (100 - int(rate_num))}] {rate_num}% {num}/{total}"
            sys.stdout.write(r)
            sys.stdout.flush()
