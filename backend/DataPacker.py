import xml.etree.cElementTree as ET

from backend.DataPackage import DataPackage
from pathlib import Path
from datetime import datetime

import os
import sys


class DataPacker:
    """数据打包器"""

    def __init__(self):
        super().__init__()

    def load(self, xml_path):
        try:
            xml_filename = Path(xml_path) / "config.xml"
            if not xml_filename.exists():
                raise RuntimeError(f"Config file not found: {xml_filename}")

            tree = ET.parse(xml_filename)
            root = tree.getroot()
            print(f"Loading packages from {xml_path}...")

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

            config_named = bool(save_node.attrib.get("config_named", "0"))
            if config_named:
                spath = spath / Path(xml_path).name
                os.makedirs(spath, exist_ok=True)

            time_named = bool(save_node.attrib.get("time_named", "0"))
            if time_named:
                spath = spath = spath = spath / datetime.now().strftime("%Y%m%d_%H%M%S")
                os.makedirs(spath, exist_ok=True)
            self.global_save_path = Path(spath)

            # 加载脚本
            for script_node in root.iter("LoadScript"):
                script_name = script_node.attrib["script_name"]
                script_file = Path(xml_path) / script_name
                flag = DataPackage.load_script(str(script_file))

            # 加载Package配置
            for package_node in root.iter("Package"):
                package = DataPackage()
                package.xml_path = xml_path
                package.global_save_path = self.global_save_path

                try:
                    package.load(package_node)
                    DataPackage.package_list.append(package)
                except Exception as e:
                    print(f"Error loading package: {e}")
                    del package
                    raise

            pkg_name_list = [p.name for p in DataPackage.package_list]
            print(f"Successfully loaded {len(DataPackage.package_list)} packages: {pkg_name_list}")

        except Exception as e:
            print(f"Error during loading config: {str(e)}")
            raise

    def input(self):
        for package in DataPackage.package_list:
            package.input()

    def exec(self):
        # 排序变化参数priority, 并执行固定参数
        for package in DataPackage.package_list:
            for p in package.all_field_list:
                if p.fixed:
                    p.pack(package.pkg_data)
                else:
                    package.field_list.append(p)
            package.field_list.sort(key=lambda x: x.priority, reverse=True)
            pl = [(p.name, p.priority, p.fixed) for p in package.field_list]

        # 每个包的每个可变参数依次执行
        flag = True
        while flag:
            for package in DataPackage.package_list:
                flag = package.pack()
                if not flag:
                    break

            # 当前包计数递增
            cur_pkg = DataPackage.global_vars["_cur_pkg"]
            max_pkg = DataPackage.global_vars["_max_pkg"]
            if cur_pkg >= max_pkg:
                break

            DataPackage.global_vars["_cur_pkg"] = cur_pkg + 1
            if cur_pkg % 1000 == 0:
                self._update_progress(cur_pkg, max_pkg)

        max_pkg = DataPackage.global_vars["_max_pkg"]
        self._update_progress(cur_pkg, max_pkg)
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
