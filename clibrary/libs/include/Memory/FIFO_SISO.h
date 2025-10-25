#ifndef _FIFO_SISO_H_
#define _FIFO_SISO_H_

///*************************************************
///@file        FIFO_SISO.h
///@author      Zhaosong
///@date        2016/05/26  created
///@version     1.0
///@brief       先进先出，单线程读单线程写的环形缓冲区.
///*************************************************

#include "IBuffer.h"

class Fifo_Siso_Private;
///@brief 环形缓冲区，支持单线程写，单线程读的无锁操作.
class MEMORY_EXPORT Fifo_Siso : public IBuffer
{
private:
    Fifo_Siso_Private* _d{nullptr};

public:
    Fifo_Siso();
    ~Fifo_Siso();

public:
    virtual float usage_rate() const override;

    ///@brief 工具函数，查询当前缓存内有效数据量.
    unsigned long long buffer_in_use() const override;

	///@brief 查询当前可用的数据量（可写字节数）.
    virtual unsigned long long buffer_free() const override;

	///@brief 查询当前缓冲区总的输入数据量.
    virtual unsigned long long bytes_input() const override;

	///@brief 查询当前缓冲区总的输出数据量.
    virtual unsigned long long bytes_output() const override;

	///@brief 返回缓冲区长度（字节数）.
    virtual unsigned long long buffer_size() const override;

	///@brief 返回一次取出的最大数据量,max_fetchable_once.
    virtual unsigned int max_front_size() const override;

public:
    ///@note 如果不设定maxBlock，则需要自己保证每次从队列中取出的数据量能整除bufSize.
    virtual int initialize(unsigned long long bufSize, unsigned int maxBlock = -1, void* = nullptr) override;

    virtual void reset(bool set_0) override;

    virtual int front(const char*& ptr, unsigned int reqSize) const override;

//FIFO操作.
public:
    virtual int push_back(const char* buf, unsigned int insSize) override; 

    virtual int pop_front(unsigned int popSize) override; 

//其他操作.
public:
    virtual int fetch_front(const char*& buf, unsigned int fetSize) override;

};
#endif
