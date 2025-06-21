cmake_minimum_required(VERSION 3.14)
project(pyevalcore_module)

find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

include(FetchContent)
FetchContent_Declare(
  pybind11
  GIT_REPOSITORY https://github.com/pybind/pybind11.git
  GIT_TAG        v2.10.4  # o versión estable reciente
)
FetchContent_MakeAvailable(pybind11)

pybind11_add_module(pyevalcore
  pyevalcore_binding.cpp
  ../../src/evaluator_serial.cpp
)

target_include_directories(pyevalcore PRIVATE ${Python3_INCLUDE_DIRS})
target_link_libraries(pyevalcore PRIVATE ${Python3_LIBRARIES})

target_include_directories(pyevalcore PRIVATE
  ${CMAKE_SOURCE_DIR}/include
)
set_target_properties(pyevalcore PROPERTIES
  CXX_STANDARD 17
  PREFIX ""
)