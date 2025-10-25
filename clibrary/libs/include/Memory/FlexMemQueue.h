#pragma once

#include <list>
#include <atomic>
#include <mutex>
#include "IBuffer.h"

using namespace std;

class MEMORY_EXPORT CFlexMemQueue : public IBuffer
{
public:
    CFlexMemQueue();
    ~CFlexMemQueue();

public:
    ///@brief 
    virtual float usage_rate() const override { return (float)(((double)m_valid_bytes) / m_max_size); }

    ///@brief 
    virtual unsigned long long buffer_in_use() const override { return m_valid_bytes; }

    ///@brief ��
    virtual unsigned long long buffer_free() const override { return m_max_size - m_valid_bytes; }

    ///@brief 
    virtual unsigned long long bytes_input() const override { return m_in_bytes; }

    ///@brief 
    virtual unsigned long long bytes_output() const override { return m_out_bytes; }

    ///@brief 
    virtual unsigned long long buffer_size() const override { return m_max_size; }

    ///@brief ,max_fetchable_once
    virtual unsigned int max_front_size() const override { return m_front_max_size; }

public:
    //�� long long _maxSize,_out_max_size�ç֧�_unit_size�˧�
    virtual int initialize(unsigned long long bufSize, unsigned int maxBlock = -1, void* extParam = nullptr) override;

    //��
    virtual void reset() override;
    virtual void reset(bool set_0) override;

    //_buf����_size
    virtual int push_back(const char *_buf, unsigned int _size) override;

    //_len
    virtual int pop_front(unsigned int _len) override;

    //�_buf, _size��
    virtual int front(const char*& _buf, unsigned int _size) const override;

    virtual int getBlockCount(){ return m_list_buf.size(); }

protected:
    //�H
    int _malloc_buf();

    //
    int free();
private:

public:
    list<char *>	m_list_buf;		//��
    list<char *>	m_idle_buf;		//��
    char			*m_tmp_buf;		//Front
    unsigned long long	m_max_size;			//��
    int					m_front_max_size;	//front
    int					m_unit_size;		//��
    atomic_llong		m_valid_bytes;		//��
    unsigned long long	m_in_bytes;			//
    unsigned long long	m_out_bytes;		//
    int         m_front_offset;				// 
    int         m_last_offset;				// ��
    char *      m_front_buf;		// 
    char *		 m_last_buf;		// 

    mutable std::mutex	m_mutex;
};
