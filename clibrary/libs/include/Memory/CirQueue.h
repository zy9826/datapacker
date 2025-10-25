/***************************************************************
* Copyright (C) 2011, Wuhan University
* All rights reserved.
*
* 文件名：	CirQueue.h
* 功能描述：一个管理循环内存的队列
*
* 当前版本：1.0
* 作    者：汪鼎文
* 完成日期：2011年4月20日
*
***************************************************************/
#pragma once

#include "IBuffer.h"
class CCirQueue_Private;
class MEMORY_EXPORT CCirQueue : public IBuffer
{
private:
    CCirQueue_Private* _d{nullptr};

public:
	CCirQueue();
	~CCirQueue();

	///@brief 查询缓存使用量，默认返回满防止误操作
    virtual float usage_rate() const override;
	
	///@brief 查询当前可读的数据量（已用字节数）
    virtual unsigned long long buffer_in_use() const override;

	///@brief 查询当前可用的数据量（可写字节数）
    virtual unsigned long long buffer_free() const override;

	///@brief 查询当前缓冲区总的输入数据量
    virtual unsigned long long bytes_input() const override;
	
	///@brief 查询当前缓冲区总的输出数据量
    virtual unsigned long long bytes_output() const override;

	///@brief 返回缓冲区长度（字节数）
    virtual unsigned long long buffer_size() const override;
	
	///@brief 返回一次取出的最大数据量,max_fetchable_once
    virtual unsigned int max_front_size() const override;

    virtual int initialize(unsigned long long bufSize, unsigned int maxBlock = -1, void* extParam = nullptr) override;

	virtual int initialize(void* buf, unsigned long long size, void* extParam) override;

    virtual int push_back(const char* buf, unsigned int insSize) override;

    virtual int pop_front(unsigned int popSize) override;

    virtual int front(const char*& ptr, unsigned int reqSize) const override;

    virtual void reset() override;
    virtual void reset(bool set_0) override;

    virtual int fetch_front(const char*& buf, unsigned int fetSize) override;

    virtual const char* buffer_address() const override;

    ///@note 不支持在尾部空间不足的情况下输入数据，此时需要通过push_back接口来处理.
    virtual char* lock_push_buffer(unsigned int lock_size) override;

    ///@note 在lock_push_buffer调用成功后调用.
    virtual int release_push_buffer(unsigned int update_size) override;
};
