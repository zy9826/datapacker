/***************************************************************
* Copyright (C) 2011, Wuhan University
* All rights reserved.
*
* 文件名：	FlexBlockMemQueue.h
* 功能描述：一个动态可增长的循环内存队列,内存整块输出，内存块的大小默认为数据帧长的整数倍，接近1M
*
* 当前版本：1.0
* 作    者：汪鼎文
* 完成日期：2016年8月17日
*
***************************************************************/
#pragma once

#include "FlexMemQueue.h"

using namespace std;

class MEMORY_EXPORT CFlexBlockMemQueue : public CFlexMemQueue
{
public:
	CFlexBlockMemQueue();
	~CFlexBlockMemQueue();

	//初始化设置分配内存队列容量 long long _max_size为最大缓存量（字节），实际大小为内存块的整数倍,_frame_size为每帧数据长度，默认1024 
	virtual int initialize(unsigned long long _max_size, unsigned int _frame_size = 1024, void* extParam = nullptr) override;

	//----新增接口----//
	//访问队首内存块，_buf为内存指针, 有整块内存时_size内存块大小，如果不足一块为实际内存大小
	int front(char* &_buf, int &_size);
	//将1个内存块数据出队
	int pop_block_front();
	//获取单位块数据大小
	int block_size() { return m_unit_size; }
	//获取数据帧长
	int frame_size() { return m_frame_size; }
	//----新增接口-END----//

private:
	int		m_frame_size;	//单位数据帧长
};
