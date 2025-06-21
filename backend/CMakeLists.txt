cmake_minimum_required(VERSION 3.14)
cmake_policy(VERSION 3.14)
# Permitir compatibilidad con CMake mínimo de dependencias antiguas (<3.5)
set(CMAKE_POLICY_VERSION_MINIMUM "3.5")
message(STATUS "CMake versión: ${CMAKE_VERSION}")

enable_testing()

project(evalcore)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

add_library(evalcore STATIC
    src/evaluator_serial.cpp
    src/evaluator_openmp.cpp
)

target_include_directories(evalcore PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)

add_executable(test_serial ../tests/test_serial.cpp)
set_target_properties(test_serial PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
target_link_libraries(test_serial PRIVATE evalcore)
target_include_directories(test_serial PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)

# GoogleTest mediante FetchContent
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
include(FetchContent)
FetchContent_Declare(
  googletest
  GIT_REPOSITORY https://github.com/google/googletest.git
  GIT_TAG v1.16.0
)
FetchContent_MakeAvailable(googletest)
target_link_libraries(test_serial PRIVATE gtest_main)
add_test(NAME serial_test COMMAND test_serial)
# OpenMP
find_package(OpenMP REQUIRED)
if (OpenMP_FOUND)
    message("OpenMP found")
    target_link_libraries(evalcore PUBLIC OpenMP::OpenMP_CXX)
endif()

add_subdirectory(bindings/py)