#ifndef CCHECKSUM_H
#define CCHECKSUM_H

#include <stdint.h>

#ifdef _WIN32
#ifdef CCHECKSUM_EXPORTS
#define CCHECKSUM_API __declspec(dllexport)
#else
#define CCHECKSUM_API __declspec(dllimport)
#endif
#else
#define CCHECKSUM_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

// 函数声明统一为uint64_t (uint8_t* bytes, int len)
// 根据不同算法自行处理传入指针和长度, 返回值统一为uint64_t, python端会根据校验字段长度处理
// 返回值大小端由python端处理, 可对应修改配置中的byteorder属性
CCHECKSUM_API uint64_t sum8bit(uint8_t* bytes, int len);
CCHECKSUM_API uint64_t sum16bit(uint8_t* bytes, int len);
CCHECKSUM_API uint64_t xor16bit(uint8_t* bytes, int len);
CCHECKSUM_API uint64_t isosum(uint8_t* bytes, int len);

#ifdef __cplusplus
}
#endif

// 结构体声明
typedef struct Point
{
    double x, y;
} Point;

#endif  // CCHECKSUM_H