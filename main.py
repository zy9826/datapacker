from backend.DataPacker import DataPacker
from pathlib import Path
from argparse import ArgumentParser

import time
import sys


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("-i", "--interactive", help="交互模式", action="store_true")
    parser.add_argument("-c", "--config_dir", help="配置文件路径")
    args = parser.parse_args()

    load_path = None
    if args.config_dir is not None:
        load_path = Path(args.config_dir)
    else:
        cur = Path("./config/")
        if not cur.exists():
            print("默认配置文件目录config不存在, 程序退出!")
            exit(1)
        dir_list = [x for x in cur.iterdir() if x.is_dir()]
        for i in range(len(dir_list)):
            print(i, Path(dir_list[i]))
        num = int(input("请选择执行方案序号:"))
        if num < 0 or num >= len(dir_list):
            print("序号错误, 程序退出!")
            exit(1)
        load_path = dir_list[num].absolute()

    packer = DataPacker()
    print(">" * 20, "开始加载配置")
    packer.load(load_path)
    if args.interactive:
        print(">" * 20, "交互模式请输入下列参数")
        packer.input()

    st = time.time()
    print(">" * 20, "开始生成数据")
    packer.exec()

    cost = (time.time() - st) * 1000
    print(f"time cost: {cost:.3f} ms")

    for i in range(3):
        sys.stdout.write(f"\r程序执行完毕, 即将退出 {3 - i}")
        time.sleep(1)
