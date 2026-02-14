import xml.etree.cElementTree as ET

from backend.DataPackage import DataPackage
from backend.processor.ProcessorBase import ProcessorBase
from pathlib import Path
from datetime import datetime

import os
import sys
from backend.formatting import format_fmt_name, resolve_fmt_value, validate_filename


class DataPacker:
    """数据打包器"""

    use_default = False  # 使用默认值
    background_mode = False  # background_mode
    progress_bar_disable = False  # 禁用进度条

    def __init__(self):
        super().__init__()
        self._cur_pkg = 0  # 当前包计数
        self._max_pkg = 0  # 最大包计数
        self._frame_len = 0
        self._total_frames = 0

    def load(self, xml_path) -> bool:
        # Runtime lifecycle assumption:
        # DataPacker runs once per process, so load() is expected to execute once.
        # Do not clear DataPackage.package_list/global_vars here by default.
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
            config_named = bool(save_node.attrib.get("config_named", False))
            time_named = bool(save_node.attrib.get("time_named", False))
        else:
            print("GlobalSavePath tag not found in config file")
            config_named = False
            time_named = False

        if not spath.exists():
            os.makedirs(spath, exist_ok=True)

        if config_named:
            spath = spath / Path(xml_path).name
            os.makedirs(spath, exist_ok=True)

        if time_named:
            spath = spath / datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs(spath, exist_ok=True)
        self.global_save_path = Path(spath)

        # 加载脚本
        for script_node in root.iter("LoadScript"):
            filename = script_node.attrib.get("script_file", "")
            if filename == "":
                raise RuntimeError(f"LoadScript Node script_file attribute is empty!")
            script_file = ProcessorBase.resolve_existing_file(filename.strip('"'), xml_path=str(xml_path), suffix=".py")
            if script_file is None or not script_file.is_file():
                raise RuntimeError(f"LoadScript file not found: {filename}")
            DataPackage.load_script(str(script_file))

        # 加载Package配置
        package_nodes = list(root.iter("Package"))
        for package_node in package_nodes:
            package = DataPackage()
            package.xml_path = xml_path
            package.global_save_path = self.global_save_path

            package.load(package_node)
            DataPackage.package_list.append(package)
            print(f"成功加载包格式<{package.name}> 包长{package.max_size}字节")

        # 计算最大包计数
        exec_pkg_list = [p for p in DataPackage.package_list if not p.not_caller]
        max_pkg_list = [p._max_pkg for p in exec_pkg_list]
        self._max_pkg = max(max_pkg_list) if len(max_pkg_list) > 0 else 0
        if self._max_pkg <= 0:
            raise RuntimeError(f"DataPacker max_pkg <= 0 {self._max_pkg}")
        frame_len_list = [p.max_size for p in exec_pkg_list]
        self._frame_len = max(frame_len_list) if len(frame_len_list) > 0 else 0
        if self._frame_len <= 0:
            raise RuntimeError(f"DataPacker frame_len <= 0 {self._frame_len}")
        self._total_frames = self._max_pkg
        DataPackage.global_vars["_max_pkg"] = self._max_pkg
        DataPackage.global_vars["_cur_pkg"] = self._cur_pkg

        # 所有节点加载完成后统一格式化保存节点文件名
        self._finalize_save_nodes(package_nodes, DataPackage.package_list)

        return True

    def _finalize_save_nodes(self, package_nodes, packages):
        for pkg_idx, package in enumerate(packages):
            for save_node in package.save_node_list:
                base_name = save_node.filename or package.name
                if save_node.fmt_name:
                    try:
                        base_name = self._format_save_node_name(save_node.fmt_name, package_nodes, packages)
                    except Exception as e:
                        print(f"[fmt_name] {package.name}-{save_node.name}: " f"format failed ({e}), fallback to package.name {package.name}")
                        base_name = package.name

                ok, reason = validate_filename(base_name)
                if not ok:
                    print(f"[fmt_name] {package.name}-{save_node.name}: " f"invalid filename '{base_name}' ({reason}), fallback to package.name {package.name}")
                    base_name = package.name

                save_node.finalize_filename(base_name)

    def _format_save_node_name(self, fmt: str, package_nodes, packages) -> str:
        return format_fmt_name(fmt, lambda token: resolve_fmt_value(token, package_nodes, packages))

    @property
    def frame_len(self) -> int:
        return self._frame_len

    @property
    def total_frames(self) -> int:
        return self._total_frames

    def exec(self, shm_producer=None):
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
                if shm_producer is not None:
                    shm_producer.write_frame(package.pkg_data)

            self._cur_pkg += 1
            DataPackage.global_vars["_cur_pkg"] = self._cur_pkg

            if self._cur_pkg % p_mod == 0 and not self.progress_bar_disable:
                if not DataPacker.background_mode:
                    self._update_progress(self._cur_pkg, self._max_pkg)
                else:
                    print(f"[Progress] {self._cur_pkg} {self._max_pkg}")
                    sys.stdout.flush()

        # 显式禁用进度条和后台模式禁用
        if not self.progress_bar_disable:
            if not DataPacker.background_mode:
                self._update_progress(self._max_pkg, self._max_pkg)
                print("\r")
            else:
                print(f"[Progress] {self._cur_pkg} {self._max_pkg}")
                sys.stdout.flush()

        # 关闭所有存储节点的文件句柄
        for package in DataPackage.package_list:
            for save_node in package.save_node_list:
                save_node.close()

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
