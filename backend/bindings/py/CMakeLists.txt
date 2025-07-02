cmake_minimum_required(VERSION 3.14)
cmake_policy(VERSION 3.14...3.26)
project(pyevalcore_module)

find_package(Python3 COMPONENTS Interpreter Development REQUIRED)

find_package(pybind11 CONFIG REQUIRED)

set(PYEVALCORE_SOURCES_TEMP_DIR "${CMAKE_CURRENT_BINARY_DIR}/temp_src")
file(MAKE_DIRECTORY "${PYEVALCORE_SOURCES_TEMP_DIR}")

file(COPY "${CMAKE_CURRENT_SOURCE_DIR}/pyevalcore_binding.cpp" DESTINATION "${PYEVALCORE_SOURCES_TEMP_DIR}")
file(COPY "${CMAKE_CURRENT_SOURCE_DIR}/../src/evaluator_serial.cpp" DESTINATION "${PYEVALCORE_SOURCES_TEMP_DIR}")
file(COPY "${CMAKE_CURRENT_SOURCE_DIR}/../src/evaluator_openmp.cpp" DESTINATION "${PYEVALCORE_SOURCES_TEMP_DIR}")
file(COPY "${CMAKE_CURRENT_SOURCE_DIR}/../src/evaluator_pthreads.cpp" DESTINATION "${PYEVALCORE_SOURCES_TEMP_DIR}")
file(COPY "${CMAKE_CURRENT_SOURCE_DIR}/../src/evaluator_cuda.cu" DESTINATION "${PYEVALCORE_SOURCES_TEMP_DIR}")

pybind11_add_module(pyevalcore
  "${PYEVALCORE_SOURCES_TEMP_DIR}/pyevalcore_binding.cpp"
  "${PYEVALCORE_SOURCES_TEMP_DIR}/evaluator_serial.cpp"
  "${PYEVALCORE_SOURCES_TEMP_DIR}/evaluator_openmp.cpp"
  "${PYEVALCORE_SOURCES_TEMP_DIR}/evaluator_pthreads.cpp"
  "${PYEVALCORE_SOURCES_TEMP_DIR}/evaluator_cuda.cu"
)

message(STATUS "CMake Source Directory: ${CMAKE_SOURCE_DIR}")
message(STATUS "CMake Current Source Directory: ${CMAKE_CURRENT_SOURCE_DIR}")
message(STATUS "Looking for CUDA file at: ${CMAKE_CURRENT_SOURCE_DIR}/../src/evaluator_cuda.cu")
find_package(CUDA REQUIRED)
enable_language(CUDA)
if(CUDA_FOUND)
# Ya se incluyó en pyevalcore_add_module
# target_sources(pyevalcore PRIVATE ../src/evaluator_cuda.cu)
target_link_libraries(pyevalcore PRIVATE CUDA::cudart)
endif()

target_include_directories(pyevalcore PRIVATE ${Python3_INCLUDE_DIRS})
target_link_libraries(pyevalcore PRIVATE ${Python3_LIBRARIES})

target_include_directories(pyevalcore PRIVATE
  ../../include
  ${CUDA_TOOLKIT_INCLUDE_DIRS}
)
set_target_properties(pyevalcore PROPERTIES
  CXX_STANDARD 17
  PREFIX ""
)