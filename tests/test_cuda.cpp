#include "gtest/gtest.h"
#include "../backend/include/evaluator.hpp"
#include <vector>
#include <numeric>
#include <chrono>
#include <iostream>

// Helper function to compare results
void compare_results(const std::vector<exam::Result>& expected, const std::vector<exam::Result>& actual) {
    ASSERT_EQ(expected.size(), actual.size());
    for (size_t i = 0; i < expected.size(); ++i) {
        EXPECT_NEAR(expected[i].score, actual[i].score, 1e-9) << "Mismatch at student " << i;
        EXPECT_EQ(expected[i].correct, actual[i].correct) << "Mismatch at student " << i;
        EXPECT_EQ(expected[i].wrong, actual[i].wrong) << "Mismatch at student " << i;
        EXPECT_EQ(expected[i].blank, actual[i].blank) << "Mismatch at student " << i;
    }
}

TEST(CudaEvaluatorTest, MatchesSerialAndOpenMP) {
    // Small dataset for testing
    const size_t num_students = 3;
    const size_t num_questions = 100;

    // Answers:
    // Student 0: All correct
    // Student 1: All wrong
    // Student 2: All blank
    std::vector<int8_t> answers(num_students * num_questions);
    for (size_t i = 0; i < num_questions; ++i) {
        answers[0 * num_questions + i] = 0; // A
        answers[1 * num_questions + i] = 1; // B
        answers[2 * num_questions + i] = -1; // Blank
    }

    // Key: All 'A' (0)
    std::vector<int8_t> key(num_questions);
    std::fill(key.begin(), key.end(), 0); // All 'A'

    exam::ScoringRule rule = {20.0, -1.125, 0.0};

    std::vector<exam::Result> results_serial(num_students);
    std::vector<exam::Result> results_openmp(num_students);
    std::vector<exam::Result> results_cuda(num_students);

    // Run Serial
    auto start_serial = std::chrono::high_resolution_clock::now();
    exam::evaluate_serial(answers.data(), num_students, key.data(), num_questions, rule, results_serial.data());
    auto end_serial = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> diff_serial = end_serial - start_serial;

    // Run OpenMP
    auto start_openmp = std::chrono::high_resolution_clock::now();
    exam::evaluate_openmp(answers.data(), num_students, key.data(), num_questions, rule, results_openmp.data());
    auto end_openmp = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> diff_openmp = end_openmp - start_openmp;

    // Run CUDA
    auto start_cuda = std::chrono::high_resolution_clock::now();
    exam::evaluate_cuda(answers.data(), num_students, key.data(), num_questions, rule, results_cuda.data());
    auto end_cuda = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double> diff_cuda = end_cuda - start_cuda;

    // Verify results
    compare_results(results_serial, results_openmp);
    compare_results(results_serial, results_cuda);

    // Print performance metrics
    std::cout << "\nPerformance Metrics (small dataset):" << std::endl;
    std::cout << "Serial Time: " << diff_serial.count() * 1000 << " ms" << std::endl;
    std::cout << "OpenMP Time: " << diff_openmp.count() * 1000 << " ms" << std::endl;
    std::cout << "CUDA Time: " << diff_cuda.count() * 1000 << " ms" << std::endl;

    if (diff_cuda.count() > 0) {
        std::cout << "Speed-up CUDA vs Serial: " << diff_serial.count() / diff_cuda.count() << "x" << std::endl;
        std::cout << "Speed-up CUDA vs OpenMP: " << diff_openmp.count() / diff_cuda.count() << "x" << std::endl;
    }
}