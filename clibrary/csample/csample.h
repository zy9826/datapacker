#ifndef CSAMPLE_H
#define CSAMPLE_H

#include <stdint.h>

#ifdef _WIN32
#ifdef CSAMPLE_EXPORTS
#define CSAMPLE_API __declspec(dllexport)
#else
#define CSAMPLE_API __declspec(dllimport)
#endif
#else
#define CSAMPLE_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

CSAMPLE_API uint64_t lshift4bit(uint8_t* bytes, int len);

#ifdef __cplusplus
}
#endif

#endif  // CSAMPLE_H