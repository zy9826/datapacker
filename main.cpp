#include <cstdint>
#include <iostream>
#include <random>
#include <vector>

#include "cchecksum.h"

// 随机生成字节数组
std::vector<uint8_t> generate_random_data(size_t length)
{
    std::vector<uint8_t> data(length);
    std::random_device rd;   // 用于生成随机种子
    std::mt19937 gen(rd());  // 使用Mersenne Twister引擎
    std::uniform_int_distribution<> dis(0, 255);

    for(size_t i = 0; i < length; ++i)
    {
        data[i] = static_cast<uint8_t>(dis(gen));
    }
    return data;
}

int main()
{
    const int num_tests = 10;       // 进行10次测试
    const size_t data_length = 10;  // 每次生成10个字节的数据

    for(int i = 0; i < num_tests; ++i)
    {
        // 生成随机数据
        std::vector<uint8_t> data = generate_random_data(data_length);

        // 调用两个函数
        uint64_t result1 = isosum(data.data(), data.size());
        uint64_t result2 = isosum2(data.data(), data.size());

        // 输出结果
        std::cout << "Test " << i + 1 << ": ";
        if(result1 == result2)
        {
            std::cout << "The results are the same." << std::endl;
        }
        else
        {
            std::cout << "The results are different." << std::endl;
        }
    }

    return 0;
}