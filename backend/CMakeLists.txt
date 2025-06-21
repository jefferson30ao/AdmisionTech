cmake_minimum_required(VERSION 3.10)

enable_testing()

project(evalcore)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

add_library(evalcore STATIC src/evaluator_serial.cpp)

target_include_directories(evalcore PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

add_executable(test_serial ../tests/test_serial.cpp)
set_target_properties(test_serial PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
target_link_libraries(test_serial PRIVATE evalcore)
target_include_directories(test_serial PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)

# Find Google Test
# Set GTest_DIR to help CMake find Google Test
set(GTest_DIR "${CMAKE_CURRENT_SOURCE_DIR}/../googletest/install/lib/cmake/GTest")
find_package(GTest CONFIG REQUIRED)
target_link_libraries(test_serial PRIVATE GTest::gtest_main GTest::gtest)
target_include_directories(test_serial PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/../googletest/include)

add_test(NAME serial_test COMMAND test_serial)
add_subdirectory(bindings/py)