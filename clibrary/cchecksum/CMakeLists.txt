cmake_minimum_required(VERSION 3.20)
project(cchecksum)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 设置C标准
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# 生成dll
add_library(cchecksum SHARED cchecksum.c)
target_compile_definitions(cchecksum PRIVATE CCHECKSUM_EXPORTS) # 定义导出宏

# 设置动态库的输出目录
# set_target_properties(cchecksum PROPERTIES
#     RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
#     LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
#     ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
# )

file(GLOB allCopyFiles  "${CMAKE_CURRENT_SOURCE_DIR}/*.h")
file(COPY ${allCopyFiles} DESTINATION ${CMAKE_BINARY_DIR}/include)

install(TARGETS ${PROJECT_NAME}
    RUNTIME DESTINATION .
    LIBRARY DESTINATION .
    ARCHIVE DESTINATION .)

