def add8bsum(ck_start, ck_size):
    global _pkg_data
    sum = 0
    for i in range(ck_start, ck_start + ck_size):
        sum = sum + _pkg_data[i]

    val = sum & 0xFFFF
    return int(val).to_bytes(2, byteorder="big")


def pyStr2Bytes(exp_str, builtin_globals, builtin_locals):
    try:
        ggg = globals()
        ggg.update(builtin_globals)
        ggg.update(builtin_locals)
        ret = eval(exp_str, ggg)
        return ret
    except Exception as e:
        raise e
