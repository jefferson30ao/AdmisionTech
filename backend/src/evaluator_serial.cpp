#include "../include/evaluator.hpp"

namespace exam {

void evaluate_serial(const int8_t* answers, size_t num_students, const int8_t* key, size_t num_questions, ScoringRule rule, Result* out) {
    for (size_t i = 0; i < num_students; ++i) {
        double score = 0.0;
        uint32_t correct = 0;
        uint32_t wrong = 0;
        uint32_t blank = 0;

        for (size_t j = 0; j < num_questions; ++j) {
            int8_t answer = answers[i * num_questions + j];
            if (answer == -1) {
                blank++;
            } else if (answer == key[j]) {
                correct++;
                score += rule.correct;
            } else if (answer >= 0 && answer <= 3) {
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