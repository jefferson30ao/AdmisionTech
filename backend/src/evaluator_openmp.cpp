#include "evaluator.hpp"
#include <omp.h>

namespace exam {

void evaluate_openmp(const int8_t* answers, size_t num_students, const int8_t* key, ScoringRule rule, Result* out) {
    #pragma omp parallel for schedule(dynamic, 64)
    for (ptrdiff_t i = 0; i < static_cast<ptrdiff_t>(num_students); ++i) {
        double score = 0;
        uint32_t correct = 0;
        uint32_t wrong = 0;
        uint32_t blank = 0;

        for (size_t j = 0; j < 100; ++j) {
            int8_t answer = answers[i * 100 + j];
            if (answer == key[j]) {
                score += rule.correct;
                correct++;
            } else if (answer == -1) {
                blank++;
            } else {
                score += rule.wrong;
                wrong++;
            }
        }

        out[i].score = score;
        out[i].correct = correct;
        out[i].wrong = wrong;
        out[i].blank = blank;
    }
}

} // namespace exam