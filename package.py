import os
import zipfile
from datetime import datetime


def main():
    # 白名单列表：留空则打包所有 dll、exe、pyd 和 config 目录，不为空则额外打包 whitelist 中的文件
    whitelist = ["iconengines", "imageformats", "platforms", "scripts", "styles", "fields_ui.xml"]  # 示例：["some.dll", "another_dir"]，留空则只打包基本项

    # 忽略列表：用于屏蔽不需要打包的 dll、exe、pyd 文件
    ignore_list = ["gen_gray_img.exe"]  # 示例：["unwanted.dll"]，添加要忽略的文件名

    current_dir = os.getcwd()
    release_dir = os.path.join(current_dir, "release")
    os.makedirs(release_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    zip_name = f"package-{timestamp}.zip"
    zip_path = os.path.join(release_dir, zip_name)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        # 总是添加 config 目录
        if os.path.exists("config"):
            for root, dirs, files in os.walk("config"):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, current_dir)
                    zipf.write(file_path, arcname)

        # 总是添加当前目录的 .dll, .exe, .pyd 文件
        for file in os.listdir("."):
            if os.path.isfile(file) and file.endswith((".dll", ".exe", ".pyd")) and file not in ignore_list:
                zipf.write(file, file)

        # 如果 whitelist 不为空，额外添加 whitelist 中的文件或目录
        if whitelist:
            for item in whitelist:
                if os.path.isfile(item):
                    zipf.write(item, item)
                elif os.path.isdir(item):
                    for root, dirs, files in os.walk(item):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, current_dir)
                            zipf.write(file_path, arcname)

    print(f"Package complete, output file: {zip_path}")


if __name__ == "__main__":
    main()
