try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

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
                cur_pkg = DataPackage.global_vars["cur_pkg"]
                DataPackage.global_vars["cur_pkg"] = cur_pkg + 1

    def load(self, xml_path):
        xml_filename = Path(xml_path) / "config.xml"
        if xml_filename.exists() is False:
            raise RuntimeError("xml file not found")

        tree = ET.parse(xml_filename)
        root = tree.getroot()
        save_node = root.find("GlobalSavePath")
        if save_node is not None:
            spath = Path(save_node.text)

            if spath.exists() is False:
                os.mkdir(spath)
            self.global_save_path = spath
        else:
            pass  # TODO: 异常处理

        for package_node in root.iter("Package"):
            package = DataPackage()
            package.xml_path = xml_path
            package.global_save_path = self.global_save_path
            package.load(package_node)
            DataPackage.package_list.append(package)

            # TODO
            # try:
            #     package.load(package_node)
            # except Exception as e:
            #     print("load xml error:", package.name, e)
            #     del package
            # else:
            #     DataPackage.package_list.append(package)


if __name__ == "__main__":
    packer = DataPacker()
    packer.load(r"C:\zhangyu\code\python\DataPacker\_config\dm256")
    packer.exec()
