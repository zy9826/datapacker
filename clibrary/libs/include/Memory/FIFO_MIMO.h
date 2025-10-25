#ifndef _FIFO_MIMO_H_
#define _FIFO_MIMO_H_

///*************************************************
///@file        FIFO_MIMO.h
///@author      Zhaosong
///@date        2016/05/27  created
///@version     1.0
///@brief       先进先出，多线程读多线程写的环形缓冲区.
///             一般用于数据无太多相关性的数据包.
///*************************************************

#include "IBuffer.h"
#include "FIFO_SISO.h"
#include <mutex>

class Fifo_Mimo : public Fifo_Siso
{
protected:
    mutable std::mutex m_inLock; ///< 输入锁.
    mutable std::mutex m_outLock; ///< 输出锁.
public:
    Fifo_Mimo();
    ~Fifo_Mimo();

public:
    virtual int front(const char*& ptr, unsigned int reqSize) const override;

//FIFO操作.  
public:
    virtual int push_back(const char* buf, unsigned int insSize) override; 

    virtual int pop_front(unsigned int popSize) override; 

};
#endif
