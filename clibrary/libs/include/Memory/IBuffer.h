#ifndef _I_BUFFER_H_
#define _I_BUFFER_H_

///*************************************************
///@file        IBuffer.h
///@author      Zhaosong
///@date        2016/05/25  created
///@version     1.0
///@brief       接口及返回值定义.
///*************************************************

#include "memory_global.h"

///@class IBuffer.
///@brief 缓冲区接口定义.
///
///预定义基本的FIFO操作和状态查询操作.
class MEMORY_EXPORT IBuffer
{
public:
	///@enum BufRetStatus
	///@brief 定义IBuffer及子类的操作返回值.
	enum BufRetStatus
	{
		BRS_FAILED = -1,
		BRS_SUCESS = 0,          ///< 操作成功 .
		BRS_FUN_NOT_IMPL,        ///< 调用的接口未实现.
		BRS_INVALID_PARAM,       ///< 参数错误.
		BRS_NOT_INIT,            ///< 未执行初始化操作.
		BRS_OUT_OF_MEM,          ///< 初始化失败，内存不足.
		BRS_LACK_OF_DATA,        ///< 有效数据量不足.
		BRS_SPACE_INSU,          ///< 存储空间不足.
	};

    IBuffer(){}
    virtual ~IBuffer(){}

	//查询接口.
public:
    ///@brief 查询缓存使用量，默认返回满防止误操作.
    virtual float usage_rate() const {return 100.0f;}

    ///@brief 查询当前可读的数据量（已用字节数）.
    virtual unsigned long long buffer_in_use() const {return 0;}

	///@brief 查询当前可用的数据量（可写字节数）.
	virtual unsigned long long buffer_free() const { return 0; }
	
	///@brief 查询当前缓冲区总的输入数据量.
	virtual unsigned long long bytes_input() const { return 0; }

	///@brief 查询当前缓冲区总的输出数据量.
	virtual unsigned long long bytes_output() const { return 0; }

    ///@brief 返回缓冲区长度（字节数）.
    virtual unsigned long long buffer_size() const {return BRS_FUN_NOT_IMPL;}

	///@brief 返回一次取出的最大数据量,max_fetchable_once.
	virtual unsigned int max_front_size() const { return 0; }

    virtual const char* buffer_address() const {return nullptr;}

	//缓冲区操作.
public:
    ///@brief 初始化缓冲区.
    ///@param bufSize [in] 指定内部缓冲区大小（字节数）.
    ///@param maxBlock [in] 设定一次front操作取出的最大数据量，一旦设定，后续操作不应超过此数值.
	///@param exeParam [in] 这个额外的参数用来.
    ///@retval 0:操作成功 / 非0：操作失败.
   virtual int initialize(unsigned long long bufSize, unsigned int maxBlock=-1, void* extParam=nullptr) = 0;
	
   ///@brief 有外部提供缓冲区，资源由外部控制.
   ///@param buf [in] 外部缓冲区地址.
   ///@param size [in] 外部缓冲区大小.
   ///@param extParam [in] 额外参数，比如ccirbuffer使用的block_size以及对应的缓冲区地址.
   virtual int initialize(void* buf, unsigned long long size, void* extParam) { return BRS_FUN_NOT_IMPL; }
    ///@brief 缓冲区复位.
    ///@note 复位内部状态.
    virtual void reset();
    virtual void reset(bool set_0) = 0;

    ///@brief 查看缓冲区前部的数据.
    ///@param ptr [out] 返回内部数据指针，指向最前面的数据.
    ///@param reqSize [in] 数据量（字节数）.
    ///@retval 0:操作成功 / 非0：操作失败.
    ///@note 约束：缓存的所有操作是事务性的，要么全部提取，要么失败.
    /// 而不是尽量对外提供数据，简化程序逻辑.
    virtual int front(const char*& ptr, unsigned int reqSize) const = 0;

	//缓冲区数据操作操作（FIFO）.
public:
    ///@brief 尾部入队.
    ///@param buf [in] 待入队的数据缓冲区.
    ///@param insSize [in] 待入队的数据量（字节数）.
    ///@retval 0:操作成功 / 非0：操作失败.
    ///@note 约束：要么全部插入，要么返回失败.
    virtual int push_back(const char* buf, unsigned int insSize) = 0;

    ///@brief 锁定并返回当前缓冲区内部数据指针，外部可直接拷贝.
    ///@note 可选实现，子类可不提供相应的操作，一旦提供则需要和release_push_buffer成对使用.
    virtual char* lock_push_buffer(unsigned int /*lock_size*/) {return nullptr;}
    ///@brief 解锁并更新当前已输入的数据量.
    ///@note 和lock_push_buffer成对使用.
    virtual int release_push_buffer(unsigned int /*update_size*/) {return BRS_FUN_NOT_IMPL;}

    ///@brief 前部出队.
    ///@param popSize [in] 出队数据量（字节数）.
    ///@retval 0:操作成功 / 非0：操作失败.
    virtual int pop_front(unsigned int popSize) = 0;

	//其他操作.
public:
    ///@brief 用来顺序提取缓存的内容，区别与读操作的另外一条数据读取操作(front).
    ///@param ptr [out] 当前提取数据位置.
    ///@param fetSize [in] 提取数据量（字节数）.
    ///@retval 返回取出的数据量，能取出数据时数据量大于0.
    ///@note 这是一个旧的接口，提供另一条访问数据内容的途径，用于在不拷贝数据的情况下保存文件等.
	/// 该操作不影响读写位置；可能返回的数值会小于fetSize.
    /// 和CCirQueue的GetBlockPoint类似，操作有细微差别，未限制一次取出的数据量.
    ///@see front
	virtual int fetch_front(const char*& /*buf*/, unsigned int /*fetSize*/) { return BRS_FUN_NOT_IMPL; }
};
#endif
