cmake_minimum_required(VERSION 3.14)
cmake_policy(VERSION 3.14)
# Permitir compatibilidad con CMake mínimo de dependencias antiguas (<3.5)
set(CMAKE_POLICY_VERSION_MINIMUM "3.5")
message(STATUS "CMake versión: ${CMAKE_VERSION}")

enable_testing()

project(evalcore LANGUAGES CXX CUDA)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Fuentes para la biblioteca evalcore
set(EVALCORE_SOURCES
    src/evaluator_serial.cpp
    src/evaluator_openmp.cpp
    src/evaluator_pthreads.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/../src/evaluator_cuda.cu
)

add_library(evalcore STATIC ${EVALCORE_SOURCES})
target_include_directories(evalcore PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)

# OpenMP
find_package(OpenMP REQUIRED COMPONENTS CXX)
if(OpenMP_FOUND)
    message(STATUS "OpenMP encontrado")
    target_link_libraries(evalcore PUBLIC OpenMP::OpenMP_CXX)
endif()

# CUDA
find_package(CUDAToolkit REQUIRED)
if(CUDAToolkit_FOUND)
    message(STATUS "CUDA Toolkit encontrado")
    target_link_libraries(evalcore PUBLIC CUDA::cudart)
    target_compile_options(evalcore PRIVATE $<$<COMPILE_LANGUAGE:CUDA>:-use_fast_math>)
endif()

# Pthreads
find_package(Threads REQUIRED)
if(Threads_FOUND)
    message(STATUS "Pthreads encontrado")
    target_link_libraries(evalcore PRIVATE Threads::Threads)
endif()

# GoogleTest via FetchContent
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
include(FetchContent)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.16.0
)
FetchContent_MakeAvailable(googletest)

# Test Serial
add_executable(test_serial ../tests/test_serial.cpp)
set_target_properties(test_serial PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
target_link_libraries(test_serial PRIVATE evalcore gtest_main)
target_include_directories(test_serial PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
add_test(NAME serial_test COMMAND test_serial)

# Test CUDA
add_executable(test_cuda ../tests/test_cuda.cpp)
set_target_properties(test_cuda PROPERTIES RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})
target_link_libraries(test_cuda PRIVATE evalcore gtest_main CUDA::cudart)
target_include_directories(test_cuda PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)
add_test(NAME cuda_test COMMAND test_cuda)