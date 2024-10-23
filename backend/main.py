import time
from DataPacker import DataPacker

from pathlib import Path

if __name__ == "__main__":
    cur = Path("./config/")

    dir_list = [x for x in cur.iterdir() if x.is_dir()]
    for i in range(len(dir_list)):
        print(i, Path(dir_list[i]))
    num = int(input("请选择执行方案序号:"))
    if num < 0 or num >= len(dir_list):
        print("序号错误")
        exit(1)

    packer = DataPacker()
    packer.load(dir_list[int(num)].absolute())
    st = time.time()
    packer.exec()
    et = time.time()
    print((et - st) * 1000, "ms")
