# CMake generated Testfile for 
# Source directory: C:/Users/jefy_/Downloads/AdmisionTech/backend
# Build directory: C:/Users/jefy_/Downloads/AdmisionTech/backend/build
# 
# This file includes the relevant testing commands required for 
# testing this directory and lists subdirectories to be tested as well.
if(CTEST_CONFIGURATION_TYPE MATCHES "^([Dd][Ee][Bb][Uu][Gg])$")
  add_test(serial_test "C:/Users/jefy_/Downloads/AdmisionTech/backend/build/Debug/test_serial.exe")
  set_tests_properties(serial_test PROPERTIES  _BACKTRACE_TRIPLES "C:/Users/jefy_/Downloads/AdmisionTech/backend/CMakeLists.txt;35;add_test;C:/Users/jefy_/Downloads/AdmisionTech/backend/CMakeLists.txt;0;")
elseif(CTEST_CONFIGURATION_TYPE MATCHES "^([Rr][Ee][Ll][Ee][Aa][Ss][Ee])$")
  add_test(serial_test "C:/Users/jefy_/Downloads/AdmisionTech/backend/build/Release/test_serial.exe")
  set_tests_properties(serial_test PROPERTIES  _BACKTRACE_TRIPLES "C:/Users/jefy_/Downloads/AdmisionTech/backend/CMakeLists.txt;35;add_test;C:/Users/jefy_/Downloads/AdmisionTech/backend/CMakeLists.txt;0;")
elseif(CTEST_CONFIGURATION_TYPE MATCHES "^([Mm][Ii][Nn][Ss][Ii][Zz][Ee][Rr][Ee][Ll])$")
  add_test(serial_test "C:/Users/jefy_/Downloads/AdmisionTech/backend/build/MinSizeRel/test_serial.exe")
  set_tests_properties(serial_test PROPERTIES  _BACKTRACE_TRIPLES "C:/Users/jefy_/Downloads/AdmisionTech/backend/CMakeLists.txt;35;add_test;C:/Users/jefy_/Downloads/AdmisionTech/backend/CMakeLists.txt;0;")
elseif(CTEST_CONFIGURATION_TYPE MATCHES "^([Rr][Ee][Ll][Ww][Ii][Tt][Hh][Dd][Ee][Bb][Ii][Nn][Ff][Oo])$")
  add_test(serial_test "C:/Users/jefy_/Downloads/AdmisionTech/backend/build/RelWithDebInfo/test_serial.exe")
  set_tests_properties(serial_test PROPERTIES  _BACKTRACE_TRIPLES "C:/Users/jefy_/Downloads/AdmisionTech/backend/CMakeLists.txt;35;add_test;C:/Users/jefy_/Downloads/AdmisionTech/backend/CMakeLists.txt;0;")
else()
  add_test(serial_test NOT_AVAILABLE)
endif()
subdirs("bindings/py")
