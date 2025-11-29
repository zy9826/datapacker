# -*- coding: utf-8 -*-
"""
自动化打包exe
功能：
1. 读取版本号（环境变量 APP_VERSION > VERSION 文件 > 默认 0.0.0.0）
2. 生成 version.txt
3. 调用 PyInstaller 打包
4. 可选：清理旧的 dist/build 文件
"""

import os
import subprocess
import shutil
from pathlib import Path

# --------------------------
# 配置
# --------------------------
VERSION_FILE = "VERSION"  # 本地版本文件
VERSION_TXT = "version.txt"  # 生成给 PyInstaller 的版本文件


# --------------------------
# 获取版本号
# --------------------------
def get_version() -> str:
    # 其次尝试从 Git 获取版本
    try:
        # 获取详细的版本信息（包含提交次数和提交哈希）
        git_describe = subprocess.check_output(["git", "describe", "--tags", "--abbrev=0"], stderr=subprocess.DEVNULL, text=True).strip()

        # 处理 git describe 的输出格式：v1.2.3
        if git_describe:
            # 移除标签前的 'v' 前缀（如果有）
            git_describe = git_describe.lstrip("v")
            return git_describe

    except (subprocess.CalledProcessError, FileNotFoundError):
        # Git 命令失败或 git 不存在，继续尝试其他方式
        pass

    ver = os.getenv("APP_VERSION")
    if ver:
        return ver.strip()
    vfile = Path(VERSION_FILE)
    if vfile.exists():
        return vfile.read_text(encoding="utf-8").strip()
    return "0.0.0.0"


# --------------------------
# 生成 version.txt
# --------------------------
def generate_version_txt(version: str):
    parts = [int(x) if x.isdigit() else 0 for x in version.split(".")]
    while len(parts) < 4:
        parts.append(0)
    version_tuple = ",".join(str(x) for x in parts[:4])

    content = f"""
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({version_tuple}),
    prodvers=({version_tuple}),
    mask=0x3f,
    flags=0x0,
    OS=0x4,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0),
  ),
  kids=[
    StringFileInfo([
      StringTable(
        "080404b0",
        [
          StringStruct("CompanyName", "ZMVison"),
          StringStruct("FileDescription", "通用数据打包软件"),
          StringStruct("FileVersion", "{version}"),
          StringStruct("InternalName", "datapacker"),
          StringStruct("LegalCopyright", "© 2025 ZMVison"),
          StringStruct("OriginalFilename", "datapacker.exe"),
          StringStruct("ProductName", "datapacker"),
          StringStruct("ProductVersion", "{version}"),
        ]
      )
    ]),
    VarFileInfo([VarStruct("Translation", [0x0804, 1200])]),
  ]
)
"""
    Path(VERSION_TXT).write_text(content, encoding="utf-8")
    Path(VERSION_FILE).write_text(version, encoding="utf-8")
    print(f"[INFO] Generated {VERSION_TXT} with version {version}")


# --------------------------
# 调用 PyInstaller
# --------------------------
def build():
    # 1. 编译 clibrary
    clib_dir = Path(__file__).parent / "clibrary"
    build_dir = clib_dir / "build"
    if not build_dir.exists():
        build_dir.mkdir(parents=True)

    print(f"[INFO] Running cmake configure in {build_dir}...")
    subprocess.check_call(["cmake", ".."], cwd=build_dir)
    print(f"[INFO] Building clibrary in {build_dir}...")
    subprocess.check_call(["cmake", "--build", ".", "--config", "Release"], cwd=build_dir)
    subprocess.check_call(["cmake", "--install", ".", "--prefix", f"{os.getcwd()}"], cwd=build_dir)

    # 2. PyInstaller 打包
    cmd = [
        "pyinstaller",
        "-Fc",  # 创建单文件可执行文件
        f"--version-file={VERSION_TXT}",  # 使用自定义版本信息
        "--add-binary=aoswrapper.pyd;.",  # 添加 aoswrapper.pyd 动态库
        "--add-binary=Memory.dll;.",  # 添加 Memory.dll 动态库
        "--add-binary=cchecksum.dll;.",  # 添加 cchecksum.dll 动态库
        "--add-binary=csample.dll;.",  # 添加 csample.dll 动态库
        "-n=datapacker",  # 指定生成的可执行文件名称
        "--add-data=VERSION:.",  # 添加 VERSION 文件
        "main.py",  # 主脚本
    ]
    print("[INFO] Running PyInstaller...")
    subprocess.check_call(cmd)
    print("[INFO] Build finished!")
    exe_target = Path("dist") / "datapacker.exe"
    if exe_target.exists():
        shutil.copy(exe_target, Path.cwd() / exe_target.name)
        print(f"[INFO] Executable created at {exe_target}")


# --------------------------
# 主流程
# --------------------------
if __name__ == "__main__":
    version = get_version()
    generate_version_txt(version)
    build()
