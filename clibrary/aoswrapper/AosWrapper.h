#ifndef AOSWRAPPER_H
#define AOSWRAPPER_H

#include <memory>

// AOS帧格式封装器，单独创建类便于保存上下文。主要封装MPDU格式

class CCirQueue;

class AosWrapper
{
public:
    AosWrapper();
    int push_back(const char* buf, unsigned int insSize);
    int make_mpdu(unsigned short& head_ptr, char* head, int mpdu_sz, bool force_pop);

private:
    int next_head_ = 0;  // 每个wrapper需要单独保存next_head上下文
    std::shared_ptr<CCirQueue> src_buf_;
};

#endif  // AOSWRAPPER_H
