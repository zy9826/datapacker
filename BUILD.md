# DataPacker 编译说明（Windows）

本文档说明如何配置 Python 虚拟环境、安装依赖，并使用 `build.py` 自动编译 CMake 工程并打包生成 `exe`。

## 环境准备

- Windows 10/11
- Python 3.8+（建议 64 位）
- CMake 3.20+（`CMakeLists.txt` 需求）
- Visual Studio Build Tools（包含 MSVC 与 Windows SDK）

注意：`clibrary/aoswrapper/CMakeLists.txt` 固定使用 `.env` 目录下的 `pybind11` 路径，所以虚拟环境目录必须为 `.env`（或自行修改该路径）。

## 1. 创建并激活虚拟环境

在工程根目录执行（PowerShell）：

```powershell
py -3 -m venv .env
.\.env\Scripts\Activate.ps1
```

若激活脚本被系统策略阻止，可先执行：

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## 2. 安装 Python 依赖

```powershell
python -m pip install -U pip
pip install -r requirements.txt
```

## 3. 可选：设置版本号

`build.py` 版本号获取优先级为：

1. `git describe --tags --long`
2. 环境变量 `APP_VERSION`
3. 根目录 `VERSION` 文件
4. 默认 `0.0.0.0`

若需要手动指定版本，可在 PowerShell 中设置：

```powershell
$env:APP_VERSION = "1.2.3.4"
```

## 4. 一键编译并打包

在工程根目录执行：

```powershell
python build.py
```

该脚本会自动完成：

1. 在 `clibrary/build` 下执行 CMake 配置与编译（Release）。
2. `cmake --install` 安装生成的 `dll/pyd` 到工程根目录。
3. 使用 PyInstaller 打包生成 `dist/datapacker.exe`。
4. 将 `dist/datapacker.exe` 复制到根目录（生成 `datapacker.exe`）。

## 输出与清理

- 最终可执行文件：
  - `dist/datapacker.exe`
  - 根目录 `datapacker.exe`
- 若需全量重建，可手动删除：
  - `clibrary/build`
  - `build`
  - `dist`

## 常见问题

- `cmake` 找不到：确认 CMake 已安装并加入 `PATH`。
- `cl.exe` 找不到：确认已安装 Visual Studio Build Tools，并在“开发者命令行/终端”或正确配置的环境中执行。
- `pybind11` 找不到：确保虚拟环境目录为 `.env`，并已执行 `pip install -r requirements.txt`。
