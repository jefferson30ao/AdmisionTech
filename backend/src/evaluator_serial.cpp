#include "../include/evaluator.hpp"

namespace exam {

void evaluate_serial(const int8_t* answers, size_t num_students, const int8_t* key, ScoringRule rule, Result* out) {
    for (size_t i = 0; i < num_students; ++i) {
        double score = 0.0;
        uint32_t correct = 0;
        uint32_t wrong = 0;
        uint32_t blank = 0;

        for (size_t j = 0; j < 100; ++j) {
            int8_t answer = answers[i * 100 + j];
            int8_t correct_answer = key[j];

            if (answer == -1) {
                blank++;
            } else if (answer == correct_answer) {
                correct++;
                score += rule.correct;
            } else {
                wrong++;
                score += rule.wrong;
            }
        }

        out[i].score = score;
        out[i].correct = correct;
        out[i].wrong = wrong;
        out[i].blank = blank;
    }
}

} // namespace exam