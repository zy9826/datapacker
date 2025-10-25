#pragma once
#include "memory_global.h"
#include <stdint.h>

//using init_cb = 

///@brief 初始化库，目前总是返回true.
extern "C" MEMORY_EXPORT bool init_allocator(void* tag);
extern "C" MEMORY_EXPORT void finit_allocator(void* tag);
///@brief 预分配大块内存供后续从其中分配小块内存使用.
///@note 多次调用可能会导致之前获取的指针失效，注意调用顺序.
extern "C" MEMORY_EXPORT void* global_alloc(void* tag, uint64_t size);
///@brief 从大块内存中申请使用小块内存.
///@note commit为true时会调用memset以确保提交内存.
extern "C" MEMORY_EXPORT void* ask_4_mem(void* tag, uint64_t size, bool commit);
