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
import sys
from pathlib import Path

# --------------------------
# 配置
# --------------------------
VERSION_FILE = "VERSION"  # 本地版本文件
VERSION_TXT = "version.txt"  # 生成给 PyInstaller 的版本文件


def run_cmd(cmd, cwd=None):
    """Run command with logging."""
    cmd_text = " ".join(str(x) for x in cmd)
    print(f"[INFO] Run: {cmd_text}")
    subprocess.check_call(cmd, cwd=str(cwd) if cwd is not None else None)


def collect_clibrary_binaries(build_dir: Path, project_root: Path):
    """
    Collect installed clibrary runtime binaries from install manifest.
    Includes all .dll/.pyd and ensures Memory.dll is included when present.
    """
    manifest = build_dir / "install_manifest.txt"
    if not manifest.exists():
        raise RuntimeError(f"install manifest not found: {manifest}")

    binaries = {}
    for line in manifest.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw:
            continue
        p = Path(raw.replace("\\", "/"))
        if p.suffix.lower() not in {".dll", ".pyd"}:
            continue

        if not p.exists():
            # Fallback: install prefix is project root
            fallback = project_root / p.name
            if fallback.exists():
                p = fallback
            else:
                continue

        binaries[p.name.lower()] = p.resolve()

    memory_dll = project_root / "Memory.dll"
    if memory_dll.exists():
        binaries.setdefault("memory.dll", memory_dll.resolve())

    if len(binaries) == 0:
        raise RuntimeError("No clibrary runtime binaries found (.dll/.pyd)")

    result = [binaries[k] for k in sorted(binaries.keys())]
    print("[INFO] Runtime binaries to bundle:")
    for p in result:
        print(f"  - {p}")
    return result


# --------------------------
# 获取版本号
# --------------------------
def get_version() -> str:
    # 其次尝试从 Git 获取版本
    try:
        # 获取详细的版本信息（包含提交次数和提交哈希）
        git_describe = subprocess.check_output(
            ["git", "describe", "--tags", "--long"],
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
        ).strip()

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
    project_root = Path(__file__).resolve().parent
    build_type = os.getenv("BUILD_TYPE", "Release")
    cmake_generator = os.getenv("CMAKE_GENERATOR", "")
    cmake_arch = os.getenv("CMAKE_ARCH", "")

    # 1. 编译 clibrary
    clib_dir = project_root / "clibrary"
    build_dir = clib_dir / "build"
    build_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Running cmake configure in {build_dir}...")
    configure_cmd = ["cmake", "..", "--fresh"]
    if cmake_generator:
        configure_cmd.extend(["-G", cmake_generator])
    if cmake_arch:
        configure_cmd.extend(["-A", cmake_arch])
    run_cmd(configure_cmd, cwd=build_dir)

    print(f"[INFO] Building clibrary in {build_dir}...")
    run_cmd(["cmake", "--build", ".", "--config", build_type], cwd=build_dir)
    run_cmd(["cmake", "--install", ".", "--prefix", str(project_root), "--config", build_type], cwd=build_dir)

    bundle_bins = collect_clibrary_binaries(build_dir, project_root)

    # 2. PyInstaller 打包
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "-Fc",  # 创建单文件可执行文件
        "--clean",
        "--noconfirm",
        f"--version-file={VERSION_TXT}",  # 使用自定义版本信息
        "-n=datapacker",  # 指定生成的可执行文件名称
        f"--add-data=VERSION{os.pathsep}.",  # 添加 VERSION 文件
    ]
    for bin_file in bundle_bins:
        cmd.append(f"--add-binary={bin_file}{os.pathsep}.")
    cmd.append("main.py")  # 主脚本

    print("[INFO] Running PyInstaller...")
    run_cmd(cmd, cwd=project_root)
    print("[INFO] Build finished!")
    exe_target = project_root / "dist" / "datapacker.exe"
    if exe_target.exists():
        onefile_target = project_root / exe_target.name
        shutil.copy(exe_target, onefile_target)
        print(f"[INFO] Executable created at {onefile_target}")


# --------------------------
# 主流程
# --------------------------
if __name__ == "__main__":
    version = get_version()
    generate_version_txt(version)
    build()
