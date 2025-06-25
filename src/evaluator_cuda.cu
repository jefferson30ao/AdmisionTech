#include <cuda_runtime.h>
#include <stdio.h>
#include <math.h> // ceil
#include <cstdint>
#include <iostream>

#include "../backend/include/evaluator.hpp"

// Definición de la clave en memoria constante
__constant__ int8_t d_key[100];

extern "C" void set_key_cuda(const int8_t* h_key) {
    cudaMemcpyToSymbol(d_key, h_key, 100 * sizeof(int8_t), 0, cudaMemcpyHostToDevice);
}

namespace exam {

// Kernel CUDA para evaluar las respuestas de los estudiantes
__global__ void evaluateKernel(const int8_t* d_answers, size_t num_students, size_t num_questions, ScoringRule rule, Result* d_results) {
    size_t student_idx = blockIdx.x * blockDim.x + threadIdx.x;

    if (student_idx < num_students) {
        uint32_t correct_count = 0;
        uint32_t wrong_count = 0;
        uint32_t blank_count = 0;
        double score = 0.0;

        for (size_t i = 0; i < num_questions; ++i) {
            int8_t student_answer = d_answers[student_idx * num_questions + i];
            int8_t correct_answer = d_key[i];

            if (student_answer == correct_answer) {
                correct_count++;
                score += rule.correct;
            } else if (student_answer == -1) {
                blank_count++;
                score += rule.blank;
            } else {
                wrong_count++;
                score += rule.wrong;
            }
        }

        d_results[student_idx].score = score;
        d_results[student_idx].correct = correct_count;
        d_results[student_idx].wrong = wrong_count;
        d_results[student_idx].blank = blank_count;
    }
}

// Función pública para invocar el kernel CUDA
void evaluate_cuda(const int8_t* h_answers, size_t num_students, const int8_t* h_key, size_t num_questions, ScoringRule rule, Result* h_results) {
    std::cout << "[CUDA] Evaluating " << num_students << " students with " << num_questions << " questions\n";
    set_key_cuda(h_key);

    int8_t* d_answers = nullptr;
    Result* d_results = nullptr;

    size_t answers_bytes = num_students * num_questions * sizeof(int8_t);
    size_t results_bytes = num_students * sizeof(Result);

    cudaMalloc((void**)&d_answers, answers_bytes);
    cudaMalloc((void**)&d_results, results_bytes);

    cudaMemcpy(d_answers, h_answers, answers_bytes, cudaMemcpyHostToDevice);

    int threadsPerBlock = 256;
    int blocksPerGrid = (int)ceil((float)num_students / threadsPerBlock);

    evaluateKernel<<<blocksPerGrid, threadsPerBlock>>>(d_answers, num_students, num_questions, rule, d_results);
    cudaDeviceSynchronize();

    cudaMemcpy(h_results, d_results, results_bytes, cudaMemcpyDeviceToHost);

    cudaFree(d_answers);
    cudaFree(d_results);

    std::cout << "[CUDA] Evaluation complete\n";
}

} // namespace exam