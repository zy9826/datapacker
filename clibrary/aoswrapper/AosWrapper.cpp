#include "AosWrapper.h"

#include <cassert>

#include "Memory/CirQueue.h"

#define HTONS(x) ((x & 0xff00) >> 8 | (x & 0x00ff) << 8)

const uint16_t MPDU_SUB_HEAD = HTONS(uint16_t(0xEA00));

AosWrapper::AosWrapper()
{
    src_buf_.reset(new CCirQueue);
    src_buf_->initialize(1024 * 1024 * 4, 2 * 1024);
}

int AosWrapper::push_back(const char* buf, unsigned int insSize)
{
    return src_buf_->push_back(buf, insSize);
}

int AosWrapper::make_mpdu(unsigned short& head_ptr, char* head, int mpdu_sz, bool force_pop)
{
    int data_sz = 0;
    const char* data_buf = nullptr;
    if(0 == src_buf_->front(data_buf, mpdu_sz + 4))
    {
        data_sz = mpdu_sz + 4;
        src_buf_->pop_front(mpdu_sz);
    }
    else if(force_pop)
    {
        data_sz = src_buf_->buffer_in_use();
        assert(data_sz < mpdu_sz + 4);
        int sz = (data_sz > mpdu_sz) ? mpdu_sz : data_sz;
        src_buf_->front(data_buf, sz);
        src_buf_->pop_front(sz);
    }

    if(data_sz <= 0)  // 无数据直接continue
        return 0;

    if(data_sz < mpdu_sz + 4)  // 数据小于MPDU包长+4，表示最后一包数据
    {
        int sz = (data_sz > mpdu_sz) ? mpdu_sz : data_sz;
        memcpy_s(head, sz, data_buf, sz);  // 拷贝数据

        if(next_head_ < mpdu_sz)  // 数据域中有下一个CCSDS包头
        {
            head_ptr = HTONS(uint16_t(next_head_));  // 填充MPDU副导头
            memset(head + sz, 0xe0, mpdu_sz - sz);   // 填充0xE0空闲包
        }
        else  // 数据域无下一包CCSDS包头，全是数据 填充0x07ff
            head_ptr = HTONS(uint16_t(0x07ff));

        // 下一个MPDU包头，考虑mpdu_sz<data_sz<mpdu_sz+4的情况
        next_head_ = (data_sz > mpdu_sz) ? (data_sz - mpdu_sz) : 0;
    }
    else
    {
        if(next_head_ < mpdu_sz)
        {
            assert(*(uint16_t*)(data_buf + next_head_) == MPDU_SUB_HEAD);

            auto pkg_len_ = HTONS(*(uint16_t*)(data_buf + next_head_ + 2));
            while(pkg_len_ + next_head_ < mpdu_sz)  // 找到mpdu_sz后的第一个包头
                pkg_len_ += HTONS(*(uint16_t*)(data_buf + next_head_ + pkg_len_ + 2));

            head_ptr = HTONS(uint16_t(next_head_));        // 填充MPDU副导头
            memcpy_s(head, mpdu_sz, data_buf, mpdu_sz);    // 拷贝数据
            next_head_ = pkg_len_ + next_head_ - mpdu_sz;  // 保存下一个MPDU包头
        }
        else
        {
            head_ptr = HTONS(uint16_t(0x07ff));          // 填充MPDU副导头
            memcpy_s(head, mpdu_sz, data_buf, mpdu_sz);  // 拷贝数据
            next_head_ -= mpdu_sz;                       // 保存下一个MPDU包头
        }
    }
    return mpdu_sz;
}
