#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>
#include "../include/evaluator.hpp"
#include <cuda_runtime.h>

namespace py = pybind11;
using namespace pybind11::literals; // to enable _a literal

PYBIND11_MODULE(pyevalcore, m) {
    m.doc() = "pyevalcore: A C++ extension for evaluating expressions.";

    py::class_<exam::ScoringRule>(m, "ScoringRule")
        .def(py::init<>())
        .def_readwrite("correct", &exam::ScoringRule::correct)
        .def_readwrite("wrong", &exam::ScoringRule::wrong)
        .def_readwrite("blank", &exam::ScoringRule::blank);

    py::class_<exam::Result>(m, "Result")
        .def(py::init<>())
        .def_readwrite("score", &exam::Result::score)
        .def_readwrite("correct", &exam::Result::correct)
        .def_readwrite("wrong", &exam::Result::wrong)
        .def_readwrite("blank", &exam::Result::blank);

    m.def("run_serial", [](py::array_t<int8_t> answers_arr, py::array_t<int8_t> key_arr, exam::ScoringRule rule) {
        py::buffer_info answers_buf = answers_arr.request();
        py::buffer_info key_buf = key_arr.request();

        if (answers_buf.ndim != 2)
            throw py::value_error("answers_arr must be a 2D array");
        if (key_buf.ndim != 1)
            throw py::value_error("key_arr must be a 1D array");

        size_t num_students = answers_buf.shape[0];
        size_t num_questions = answers_buf.shape[1];

        if (num_questions != key_buf.shape[0])
            throw py::value_error("Number of questions in answers_arr must match length of key_arr");

        const int8_t* answers_ptr = static_cast<int8_t*>(answers_buf.ptr);
        const int8_t* key_ptr = static_cast<int8_t*>(key_buf.ptr);

        std::vector<exam::Result> results(num_students);
        exam::evaluate_serial(answers_ptr, num_students, key_ptr, num_questions, rule, results.data());

        // Convert results to a list of dictionaries for easier DataFrame conversion in Python
        py::list py_results;
        for (const auto& res : results) {
            py_results.append(py::dict(
                "score"_a = res.score,
                "correct"_a = res.correct,
                "wrong"_a = res.wrong,
                "blank"_a = res.blank
            ));
        }
        return py_results;
    }, "Evaluates answers in serial mode.");

    m.def("get_device_count", [](){
        int count;
        cudaGetDeviceCount(&count);
        return count;
    }, "Returns the number of CUDA devices available.");

    m.def("run_cuda", [](py::array_t<int8_t> answers_arr, py::array_t<int8_t> key_arr, exam::ScoringRule rule) {
        py::buffer_info answers_buf = answers_arr.request();
        py::buffer_info key_buf = key_arr.request();

        if (answers_buf.ndim != 2)
            throw py::value_error("answers_arr must be a 2D array");
        if (key_buf.ndim != 1)
            throw py::value_error("key_arr must be a 1D array");

        size_t num_students = answers_buf.shape[0];
        size_t num_questions = answers_buf.shape[1];

        if (num_questions != key_buf.shape[0])
            throw py::value_error("Number of questions in answers_arr must match length of key_arr");

        const int8_t* answers_ptr = static_cast<int8_t*>(answers_buf.ptr);
        const int8_t* key_ptr = static_cast<int8_t*>(key_buf.ptr);

        std::vector<exam::Result> results(num_students);
        exam::evaluate_cuda(answers_ptr, num_students, key_ptr, num_questions, rule, results.data());

        // Convert results to a list of dictionaries for easier DataFrame conversion in Python
        py::list py_results;
        for (const auto& res : results) {
            py_results.append(py::dict(
                "score"_a = res.score,
                "correct"_a = res.correct,
                "wrong"_a = res.wrong,
                "blank"_a = res.blank
            ));
        }
        return py_results;
    }, "Evaluates answers in CUDA mode.");

    m.def("run_openmp", [](py::array_t<int8_t> answers_arr, py::array_t<int8_t> key_arr, exam::ScoringRule rule) {
        py::buffer_info answers_buf = answers_arr.request();
        py::buffer_info key_buf = key_arr.request();

        if (answers_buf.ndim != 2)
            throw py::value_error("answers_arr must be a 2D array");
        if (key_buf.ndim != 1)
            throw py::value_error("key_arr must be a 1D array");

        size_t num_students = answers_buf.shape[0];
        size_t num_questions = answers_buf.shape[1];

        if (num_questions != key_buf.shape[0])
            throw py::value_error("Number of questions in answers_arr must match length of key_arr");

        const int8_t* answers_ptr = static_cast<int8_t*>(answers_buf.ptr);
        const int8_t* key_ptr = static_cast<int8_t*>(key_buf.ptr);

        std::vector<exam::Result> results(num_students);
        exam::evaluate_openmp(answers_ptr, num_students, key_ptr, num_questions, rule, results.data());

        // Convert results to a list of dictionaries for easier DataFrame conversion in Python
        py::list py_results;
        for (const auto& res : results) {
            py_results.append(py::dict(
                "score"_a = res.score,
                "correct"_a = res.correct,
                "wrong"_a = res.wrong,
                "blank"_a = res.blank
            ));
        }
        return py_results;
    }, "Evaluates answers in OpenMP mode.");

    m.def("run_pthreads", [](py::array_t<int8_t> answers_arr, py::array_t<int8_t> key_arr, exam::ScoringRule rule) {
        py::buffer_info answers_buf = answers_arr.request();
        py::buffer_info key_buf = key_arr.request();

        if (answers_buf.ndim != 2)
            throw py::value_error("answers_arr must be a 2D array");
        if (key_buf.ndim != 1)
            throw py::value_error("key_arr must be a 1D array");

        size_t num_students = answers_buf.shape[0];
        size_t num_questions = answers_buf.shape[1];

        if (num_questions != key_buf.shape[0])
            throw py::value_error("Number of questions in answers_arr must match length of key_arr");

        const int8_t* answers_ptr = static_cast<int8_t*>(answers_buf.ptr);
        const int8_t* key_ptr = static_cast<int8_t*>(key_buf.ptr);

        std::vector<exam::Result> results(num_students);
        exam::evaluate_pthreads(answers_ptr, num_students, key_ptr, num_questions, rule, results.data());

        // Convert results to a list of dictionaries for easier DataFrame conversion in Python
        py::list py_results;
        for (const auto& res : results) {
            py_results.append(py::dict(
                "score"_a = res.score,
                "correct"_a = res.correct,
                "wrong"_a = res.wrong,
                "blank"_a = res.blank
            ));
        }
        return py_results;
    }, "Evaluates answers in pthreads mode.");
}