cmake_minimum_required(VERSION 3.20)
project(aoswrapper LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)


# 查找python和pybind11
set(pybind11_DIR "${CMAKE_CURRENT_LIST_DIR}\\..\\..\\.env\\Lib\\site-packages\\pybind11\\share\\cmake\\pybind11")
find_package(Python REQUIRED COMPONENTS Interpreter Development)
find_package(pybind11 REQUIRED)

add_library(${PROJECT_NAME} MODULE
    AosWrapper.cpp
    bindings/pybind_AosWrapper.cpp
)

target_include_directories(${PROJECT_NAME} PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_LIST_DIR}\\..\\libs\\include
)
target_link_directories(${PROJECT_NAME} PRIVATE
    ${CMAKE_CURRENT_LIST_DIR}\\..\\libs\\release
)
target_link_libraries(${PROJECT_NAME} PRIVATE
    pybind11::module
    Memory
)

# 设置动态库的输出目录
set_target_properties(${PROJECT_NAME} PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

file(GLOB allCopyFiles  "${CMAKE_CURRENT_SOURCE_DIR}/*.h" "${CMAKE_CURRENT_SOURCE_DIR}/bindings/*.h")
file(COPY ${allCopyFiles} DESTINATION ${CMAKE_BINARY_DIR}/include)
file(COPY "${CMAKE_CURRENT_LIST_DIR}\\..\\libs\\release\\Memory.dll" DESTINATION "${CMAKE_BINARY_DIR}/bin/Release")


# 处理 Windows 模块命名（去掉 lib 前缀，并改成 .pyd）
if (WIN32)
    set_target_properties(${PROJECT_NAME} PROPERTIES
        PREFIX ""
        SUFFIX ".pyd"
    )
endif()
