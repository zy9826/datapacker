from backend.DataPacker import DataPacker
from backend.DataPackage import DataPackage
from backend.Console import console
from pathlib import Path
from argparse import ArgumentParser
from multiprocessing import shared_memory


import time
import os
import sys

import cProfile
import pstats


enable_test = False


def get_version() -> str:
    if getattr(sys, "frozen", False):  # exe 打包模式
        base_path = sys._MEIPASS
    else:
        base_path = Path(__file__).parent
    return Path(base_path, "VERSION").read_text(encoding="utf-8").strip()


def start(args, shm=None):
    print(f"datapacker v{get_version()}")

    load_path = None
    if args.config_dir is not None:
        load_path = Path(args.config_dir)
    else:
        cur = Path("./config/")
        if not cur.exists():
            raise RuntimeError("默认配置文件目录config不存在")

        dir_list = [x for x in cur.iterdir() if x.is_dir() and not str(x.name).startswith("__")]
        dir_num = len(dir_list)
        if args.config_num is not None:
            num = int(args.config_num)
        else:
            console.print("=====>", "请选择配置文件", "<=====", style="bold white")
            for i in range(dir_num):
                console.print(i, Path(dir_list[i].name))
            num = int(console.input(f"[bold green]请选择执行方案序号[0-{dir_num-1}]:[/]"))

        if num < 0 or num >= dir_num:
            raise RuntimeError("选择方案序号错误")
        load_path = dir_list[num].absolute()

    packer = DataPacker()
    DataPacker.use_default = DataPackage.use_default = args.use_default  # 使用配置的默认参数
    DataPacker.background_mode = DataPackage.background_mode = args.background_mode  # background_mode
    DataPacker.progress_bar_disable = args.progress_bar_disable  # 禁用进度条

    console.print("\n=====>", "开始加载配置", "<=====", style="bold white")
    flag = packer.load(load_path)
    if not flag:
        raise RuntimeError("加载配置文件失败")

    if enable_test or args.test_flag is not None:
        profiler = cProfile.Profile()
        profiler.enable()

    console.print("\n=====>", "开始生成数据", "<=====", style="bold white")
    st = time.time()
    packer.exec(shm)
    cost = (time.time() - st) * 1000
    print(f"生成完成, 耗时: {cost:.3f} ms")

    if enable_test or args.test_flag is not None:
        stats = pstats.Stats(profiler)
        stats.sort_stats("cumulative")
        amount = 30 if args.test_flag <= 0 else args.test_flag
        stats.print_stats(amount)

    if not args.background_mode:
        print(f"保存路径: {packer.global_save_path}")
        text = console.input("[bold yellow]【程序退出后落盘】[/bold yellow]输入Enter直接退出, 输入任意字符+Enter打开保存路径后退出:")
        if text:
            os.system(f"start explorer {packer.global_save_path}")
    else:  # background_mode
        print(f"[SavePath] {Path(packer.global_save_path).resolve()}")
    return True


if __name__ == "__main__":
    parser = ArgumentParser()
    # 调试使用配置文件参数时可将 store_true(默认) 改为 store_false
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-u", "--use_default", help="使用默认参数运行, 确保配置文件满足参数需求", action="store_true")
    group.add_argument("-b", "--background_mode", help="后台模式运行, 使用配置文件中的input_value参数运行", action="store_true")

    parser.add_argument("-c", "--config_dir", help="配置文件路径")
    parser.add_argument("-n", "--config_num", type=int, default=None, help="配置文件序号")
    parser.add_argument("-s", "--shm_token", type=str, default=None, help="shared memory token, only background mode use")
    parser.add_argument("-p", "--progress_bar_disable", help="禁用显示进度条", action="store_true")
    parser.add_argument("-t", "--test_flag", type=int, help="测试模式, -t n:开启测试模式, 显示n个最耗时函数, 用于分析耗时")
    args = parser.parse_args()

    ret = False
    # ret = start(args)
    try:
        # 初始化共享内存
        shm = None
        if args.background_mode and args.shm_token is not None:
            shm = shared_memory.SharedMemory(name=args.shm_token)
            if shm.size != 10240:
                shm = None
                raise RuntimeError("shared memory size error")
            if int.from_bytes(shm.buf[0:4]) != 0xD2029649:
                shm = None
                raise RuntimeError("frame header error")

        ret = start(args, shm)
    except Exception as e:
        console.print("[ERROR] " + str(e), style="bold red")

        if args.background_mode and shm is not None:
            msg_cnt = int.from_bytes(shm.buf[12:13])
            idx = msg_cnt % 8
            pos = 2048 + idx * 1024
            msg_bytes = str(e).encode("utf-8")
            msg_len = len(msg_bytes)
            if msg_len > 1024:
                msg_len = 1024
            shm.buf[pos : pos + msg_len] = msg_bytes[0:msg_len]  # 更新消息
            shm.buf[12:13] = int((msg_cnt + 1) & 0xFF).to_bytes(1, "little")  # 更新消息计数

    if not args.background_mode:
        if not ret:
            c = input("执行出错请检查报错信息, 输入Enter退出: ")
    else:
        if shm is not None:
            shm.close()
            shm.unlink()

    if ret:
        sys.exit(0)
    else:
        sys.exit(-1)
