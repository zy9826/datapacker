from backend.DataPacker import DataPacker
from backend.DataPackage import DataPackage
from backend.Console import console
from pathlib import Path
from argparse import ArgumentParser


import time
import os

import cProfile
import pstats


enable_test = False


def start(args):
    load_path = None
    if args.config_dir is not None:
        load_path = Path(args.config_dir)
    else:
        cur = Path("./config/")
        if not cur.exists():
            raise RuntimeError("默认配置文件目录config不存在")

        dir_list = [x for x in cur.iterdir() if x.is_dir() and not str(x.name).startswith("__")]
        if args.config_num is not None:
            num = int(args.config_num)
        else:
            console.print("=====>", "请选择配置文件", "<=====", style="bold white")
            dir_num = len(dir_list)
            for i in range(dir_num):
                console.print(i, Path(dir_list[i].name))
            num = int(console.input(f"[bold green]请选择执行方案序号[0-{dir_num-1}]:[/]"))

        if num < 0 or num >= dir_num:
            raise RuntimeError("选择方案序号错误")
        load_path = dir_list[num].absolute()

    # 默认为交互模式
    if args.interactive == args.use_default == args.backend == False:
        args.interactive = True

    packer = DataPacker()
    DataPacker.interactive = DataPackage.interactive = args.interactive  # 交互式输入参数
    DataPacker.use_default = DataPackage.use_default = args.use_default  # 使用配置的默认参数
    DataPacker.backend = DataPackage.backend = args.backend  # backend模式

    console.print("\n=====>", "开始加载配置", "<=====", style="bold white")
    flag = packer.load(load_path)
    if not flag:
        raise RuntimeError("加载配置文件失败")

    if enable_test or args.test_flag is not None:
        profiler = cProfile.Profile()
        profiler.enable()

    console.print("\n=====>", "开始生成数据", "<=====", style="bold white")
    st = time.time()
    packer.exec()
    cost = (time.time() - st) * 1000
    print(f"耗时: {cost:.3f} ms")

    if enable_test or args.test_flag is not None:
        stats = pstats.Stats(profiler)
        stats.sort_stats("cumulative")
        amount = 30 if args.test_flag <= 0 else args.test_flag
        stats.print_stats(amount)

    print(f"保存路径: {packer.global_save_path}")
    text = console.input("[bold yellow]【程序退出后落盘】[/bold yellow]输入Enter直接退出, 输入任意字符+Enter打开保存路径后退出:")
    if text:
        os.system(f"start explorer {packer.global_save_path}")
    return True


if __name__ == "__main__":
    parser = ArgumentParser()
    # 调试使用配置文件参数时可将 store_true(默认) 改为 store_false
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("-i", "--interactive", help="交互式输入参数, 默认运行方式", action="store_true")
    group.add_argument("-u", "--use_default", help="使用默认参数运行, 确保配置文件满足参数需求", action="store_true")
    group.add_argument("-b", "--backend", help="使用配置文件中的input_value参数运行, 默认值False", action="store_true")

    parser.add_argument("-c", "--config_dir", help="配置文件路径")
    parser.add_argument("-n", "--config_num", type=int, default=None, help="配置文件序号")
    parser.add_argument("-t", "--test_flag", type=int, help="测试模式, -t n:开启测试模式, 显示n个最耗时函数, 用于分析耗时")
    args = parser.parse_args()

    ret = False
    # ret = start(args)
    try:
        ret = start(args)
    except Exception as e:
        console.print("[ERROR] " + str(e), style="bold red")

    if not ret:
        c = input("执行出错请检查报错信息, 输入Enter退出: ")
