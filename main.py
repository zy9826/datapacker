from backend.DataPacker import DataPacker

from pathlib import Path

import time
import sys
import os


if __name__ == "__main__":
    load_path = None
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        load_path = Path(sys.argv[1])
    else:
        cur = Path("./config/")
        dir_list = [x for x in cur.iterdir() if x.is_dir()]
        for i in range(len(dir_list)):
            print(i, Path(dir_list[i]))
        num = int(input("请选择执行方案序号:"))
        if num < 0 or num >= len(dir_list):
            print("序号错误, 程序退出!")
            exit(1)
        load_path = dir_list[num].absolute()

    packer = DataPacker()
    packer.load(load_path)
    st = time.time()
    packer.exec()

    cost = (time.time() - st) * 1000
    print(f"time cost: {cost:.3f} ms")
    input("程序执行完毕, 按Enter键退出!")
