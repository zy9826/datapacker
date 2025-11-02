#include "cchecksum.h"

uint16_t HTONS(uint16_t x)
{
    return ((x >> 8) & 0xFF) | ((x << 8) & 0xFF00);
}

// 8bit求和
uint64_t sum8bit(uint8_t* bytes, int len)
{
    uint64_t sum = 0;
    for(int i = 0; i < len; i++)
        sum += bytes[i];
    return sum;
}

uint64_t sum16bit(uint8_t* bytes, int len)
{
    uint64_t sum = 0;
    for(int i = 0; i < len; i += 2)
    {
        uint8_t temp[2] = {bytes[i + 1], bytes[i]};
        sum += *(uint16_t*)(temp);
    }
    return sum;
}

uint64_t xor8bit(uint8_t* bytes, int len)
{
    uint8_t xorl = 0;
    for(int i = 0; i < len; i++)
        xorl ^= bytes[i];
    return xorl;
}

uint64_t xor16bit(uint8_t* bytes, int len)
{
    uint8_t xorl = 0;
    uint8_t xorh = 0;
    for(int i = 0; i < len; i += 2)
    {
        xorh ^= bytes[i];
        xorl ^= bytes[i + 1];
    }
    // 奇数长度
    if(len % 2 == 1)
        xorh ^= bytes[len - 1];

    return (xorh << 8) | xorl;
}

uint64_t isosum(uint8_t* bytes, int len)
{
    uint32_t c0 = 0;
    uint32_t c1 = 0;

    for(int i = 0; i < len; i++)
    {
        c0 = c0 + bytes[i];
        c1 = c1 + (len - i) * bytes[i];
    }
    c0 = c0 % 0xff;
    c1 = c1 % 0xff;

    uint8_t temp = (c0 + c1) % 0xff;
    temp = 0xff - temp;
    if(temp == 0)
        temp = 0xff;
    if(c1 == 0)
        c1 = 0xff;
    return (uint16_t)(c1 | (temp << 8));
}

uint64_t udp_checksum(uint8_t* bytes, int len)
{
    uint32_t sum = 0;
    uint16_t* ptr = (uint16_t*)bytes;
    int sz = len >> 1;
    while(sz-- > 0)
        sum += HTONS(*ptr++);

    if((len & 0x1ul) == 1)
        sum += (uint8_t)(*(bytes + len - 1)) << 8;

    sum = (sum >> 16) + (sum & 0xfffful);
    sum += (sum >> 16);
    return ~HTONS((uint16_t)sum);
}