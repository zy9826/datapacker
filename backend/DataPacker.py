from xml_utils import ET  # 从xml_utils导入ET

from DataPackage import DataPackage
from pathlib import Path

import os


class DataPacker:
    """数据打包器"""

    def __init__(self):
        pass

    def exec(self):
        flag = True
        while flag:
            for package in DataPackage.package_list:
                flag = package.pack()
                if flag is False:
                    break

            # 当前包计数递增
            cur_pkg = DataPackage.global_vars["_cur_pkg"]
            DataPackage.global_vars["_cur_pkg"] = cur_pkg + 1

    def load(self, xml_path):
        xml_filename = Path(xml_path) / "config.xml"
        if xml_filename.exists() is False:
            raise RuntimeError("load xml file not found")

        tree = ET.parse(xml_filename)
        root = tree.getroot()
        save_node = root.find("GlobalSavePath")
        if save_node is not None:
            spath = Path(save_node.text)

            if spath.exists() is False:
                os.makedirs(spath)
            self.global_save_path = spath
        else:
            raise RuntimeError("GlobalSavePath tag not found")

        for package_node in root.iter("Package"):
            package = DataPackage()
            package.xml_path = xml_path
            package.global_save_path = self.global_save_path

            try:
                package.load(package_node)
                DataPackage.package_list.append(package)
            except Exception as e:
                del package
                raise e
