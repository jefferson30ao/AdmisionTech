cmake_minimum_required(VERSION 3.14)
cmake_policy(VERSION 3.14...3.26)
project(pyevalcore_module)

find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(pyevalcore
  pyevalcore_binding.cpp
  ../../src/evaluator_serial.cpp
  ../../src/evaluator_openmp.cpp
)

message(STATUS "CMake Source Directory: ${CMAKE_SOURCE_DIR}")
message(STATUS "CMake Current Source Directory: ${CMAKE_CURRENT_SOURCE_DIR}")
message(STATUS "Looking for CUDA file at: ${CMAKE_CURRENT_SOURCE_DIR}/../../../src/evaluator_cuda.cu")
find_package(CUDAToolkit REQUIRED)
enable_language(CUDA)
if(CUDAToolkit_FOUND)
  target_sources(pyevalcore PRIVATE ../../../src/evaluator_cuda.cu)
  target_link_libraries(pyevalcore PRIVATE CUDAToolkit::cudart)
endif()

target_include_directories(pyevalcore PRIVATE ${Python3_INCLUDE_DIRS})
target_link_libraries(pyevalcore PRIVATE ${Python3_LIBRARIES})

target_include_directories(pyevalcore PRIVATE
  ${CMAKE_SOURCE_DIR}/include
)
set_target_properties(pyevalcore PROPERTIES
  CXX_STANDARD 17
  PREFIX ""
)