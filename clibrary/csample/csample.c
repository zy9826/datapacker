#include "csample.h"

uint64_t lshift4bit(uint8_t* bytes, int len)
{
    int half_len = len / 2;
    for(int i = half_len - 1; i >= 0; i--)
    {
        uint16_t tmp = (uint16_t)(bytes[i]) << 4;
        *(uint16_t*)(bytes + i * 2) = (tmp << 8) | ((tmp & 0xff00) >> 8);
    }
    return len;
}