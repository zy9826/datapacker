from backend.DataPacker import DataPacker
from backend.DataPackage import DataPackage
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
            print("默认配置文件目录config不存在, 程序退出!")
            return False

        dir_list = [x for x in cur.iterdir() if x.is_dir()]
        if args.config_num is not None:
            num = int(args.config_num)
        else:
            for i in range(len(dir_list)):
                print(i, Path(dir_list[i].name))
            num = int(input("请选择执行方案序号:"))

        if num < 0 or num >= len(dir_list):
            print("序号错误, 程序退出!")
            return False
        load_path = dir_list[num].absolute()

    packer = DataPacker()
    DataPacker.interactive = not args.use_default_param
    DataPackage.interactive = not args.use_default_param
    print("=====>", "开始加载配置", "<=====")
    flag = packer.load(load_path)
    if not flag:
        print("加载配置出错, 程序退出!")
        return False

    if enable_test or args.test_flag is not None:
        profiler = cProfile.Profile()
        profiler.enable()

    print("=====>", "开始生成数据", "<=====")
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
    text = input("输入Enter直接退出, 输入任意字符+Enter打开保存路径:")
    if text:
        os.system(f"start explorer {packer.global_save_path}")
    return True


if __name__ == "__main__":
    parser = ArgumentParser()
    # 调试使用配置文件参数时可将 store_true(默认) 改为 store_false
    parser.add_argument("-u", "--use_default_param", help="使用默认参数运行, 确保配置文件满足参数需求", action="store_true")
    parser.add_argument("-c", "--config_dir", help="配置文件路径")
    parser.add_argument("-n", "--config_num", type=int, default=None, help="配置文件序号")
    parser.add_argument("-t", "--test_flag", type=int, help="测试模式, -t n:开启测试模式, 显示n个最耗时函数, 用于分析耗时")
    args = parser.parse_args()

    ret = False
    # ret = start(args)
    try:
        ret = start(args)
    except Exception as e:
        print(e)

    if not ret:
        c = input("执行出错请检查报错信息, 输入Enter退出: ")
