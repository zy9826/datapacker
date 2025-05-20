#include "csample.h"

uint64_t lshift4bit(uint8_t* bytes, int len)
{
    int times = len / 3;
    for(int i = times - 1; i >= 0; i--)
    {
        int s_ofs = i * 2;
        uint8_t B1 = bytes[s_ofs];
        uint8_t B2 = bytes[s_ofs + 1];

        int d_ofs = i * 3;
        bytes[d_ofs] = B1;
        bytes[d_ofs + 1] = (B2 >> 4) & 0x0F;
        bytes[d_ofs + 2] = (B2 & 0x0F) << 4;
    }
    return len;
}

uint64_t lshift8bit(uint8_t* bytes, int len, int lshift)
{
    int times = len / 2;
    for(int i = times - 1; i >= 0; i--)
    {
        int s_ofs = i;
        uint16_t val = bytes[s_ofs];
        val <<= lshift;
        int d_ofs = i * 2;
        bytes[d_ofs] = val >> 8;
        bytes[d_ofs + 1] = val & 0xFF;
    }
    return len;
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