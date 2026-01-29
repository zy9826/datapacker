import xml.etree.cElementTree as ET

from backend.DataPackage import DataPackage
from pathlib import Path
from datetime import datetime

import os
import sys


class DataPacker:
    """数据打包器"""

    use_default = False  # 使用默认值
    background_mode = False  # background_mode
    progress_bar_disable = False  # 禁用进度条

    def __init__(self):
        super().__init__()
        self._cur_pkg = 0  # 当前包计数
        self._max_pkg = 0  # 最大包计数

    def load(self, xml_path) -> bool:
        if Path(xml_path).is_dir():
            xml_filename = Path(xml_path) / "config.xml"
        else:
            xml_filename = Path(xml_path)
            xml_path = xml_filename.parent

        if not xml_filename.exists():
            raise RuntimeError(f"Config file not found: {xml_filename}")

        tree = ET.parse(xml_filename)
        root = tree.getroot()
        print(f"加载配置: {xml_filename}")

        # 加载全局保存路径
        spath = Path.cwd() / "output"
        save_node = root.find("GlobalSavePath")
        if save_node is not None:
            spath = Path(save_node.attrib.get("save_path", Path.cwd() / "output"))
        else:
            print("GlobalSavePath tag not found in config file")

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
                raise RuntimeError(f"LoadScript Node script_file attribute is empty!")
            script_file = Path(xml_path) / filename
            flag = DataPackage.load_script(str(script_file))

        # 加载Package配置
        for package_node in root.iter("Package"):
            package = DataPackage()
            package.xml_path = xml_path
            package.global_save_path = self.global_save_path

            package.load(package_node)
            DataPackage.package_list.append(package)
            print(f"成功加载包格式<{package.name}> 包长{package.max_size}字节")

        # 计算最大包计数
        max_pkg_list = [p._max_pkg for p in DataPackage.package_list if not p.not_caller]
        self._max_pkg = max(max_pkg_list) if len(max_pkg_list) > 0 else 0
        if self._max_pkg <= 0:
            raise RuntimeError(f"DataPacker max_pkg <= 0 {self._max_pkg}")
        DataPackage.global_vars["_max_pkg"] = self._max_pkg
        DataPackage.global_vars["_cur_pkg"] = self._cur_pkg

        return True

    def exec(self, shm=None):
        p_mod = self._max_pkg // 100
        if p_mod < 10:
            p_mod = 10
        if self.progress_bar_disable:
            print("已禁用进度条显示!")

        # 每个包的每个可变参数依次执行
        flag = True
        exec_pkg_list = [p for p in DataPackage.package_list if not p.not_caller]
        while self._cur_pkg < self._max_pkg:
            for package in exec_pkg_list:
                flag = package.pack()
                if not flag:
                    continue

            self._cur_pkg += 1
            DataPackage.global_vars["_cur_pkg"] = self._cur_pkg

            if self._cur_pkg % p_mod == 0 and not self.progress_bar_disable:
                if not DataPacker.background_mode:
                    self._update_progress(self._cur_pkg, self._max_pkg)
                else:
                    if shm is not None:
                        shm.buf[4:8] = self._cur_pkg.to_bytes(4, "little")
                        shm.buf[8:12] = self._max_pkg.to_bytes(4, "little")
                    else:
                        print(f"[Progress] {self._cur_pkg} {self._max_pkg}")
                        sys.stdout.flush()

        # 显式禁用进度条和后台模式禁用
        if not self.progress_bar_disable:
            if not DataPacker.background_mode:
                self._update_progress(self._max_pkg, self._max_pkg)
                print("\r")
            else:
                if shm is not None:
                    shm.buf[4:8] = self._cur_pkg.to_bytes(4, "little")
                    shm.buf[8:12] = self._max_pkg.to_bytes(4, "little")
                else:
                    print(f"[Progress] {self._cur_pkg} {self._max_pkg}")
                    sys.stdout.flush()

    def _update_progress(self, num, total):
        rate = num / total
        rate_num = int(rate * 100)
        max_char = len(str(total))  # 计算数字长度
        try:
            terminal_width = os.get_terminal_size().columns  # 获取终端宽度
            bar_length = terminal_width - (12 + max_char * 2)  # 预留显示百分比和数字的空间
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
