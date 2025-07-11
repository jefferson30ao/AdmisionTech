#ifndef EVALUATOR_HPP
#define EVALUATOR_HPP

#include <cstdint>
#include <cstddef>

namespace exam {

struct ScoringRule {
    double correct;
    double wrong;
    double blank;
};

struct Result {
    double score;
    uint32_t correct;
    uint32_t wrong;
    uint32_t blank;
};

enum class Mode { Serial, OpenMP, Cuda, Pthreads };

void evaluate_serial(const int8_t* answers, size_t num_students, const int8_t* key, size_t num_questions, ScoringRule rule, Result* out);
void evaluate_openmp(const int8_t* answers, size_t num_students, const int8_t* key, size_t num_questions, ScoringRule rule, Result* out);
void evaluate_cuda(const int8_t* answers, size_t num_students, const int8_t* key, size_t num_questions, ScoringRule rule, Result* out);
void evaluate_pthreads(const int8_t* answers, size_t num_students, const int8_t* key, size_t num_questions, ScoringRule rule, Result* out);

} // namespace exam

#endif // EVALUATOR_HPP