#include <iostream>
#include "gtest/gtest.h"
#include "evaluator.hpp"
#include <cassert>

using namespace exam; // Add this line to use the exam namespace

TEST(SerialTest, Correct) {
    int8_t answers[15] = {
        1, 2, 3, 4, 1,
        1, 2, 3, 4, 1,
        1, 2, 3, 4, 1
    };
    int8_t key[5] = {1, 2, 3, 4, 1};
    ScoringRule rule = {1, 0, 0};
    Result result[3];

    evaluate_serial(answers, 3, key, rule, result);

    for (int i = 0; i < 3; ++i) {
        ASSERT_EQ(result[i].correct, 5);
        ASSERT_EQ(result[i].wrong, 0);
        ASSERT_EQ(result[i].blank, 0);
        ASSERT_EQ(result[i].score, 5);
    }
}

TEST(SerialTest, StudentAnswers) {
    int8_t answers[] = {
        1, 2, -1, 1, 2,
        2, 1, 2, -1, 1,
        -1, 2, 1, 2, 1
    };
    int8_t key[5] = {1, 2, 1, 2, 1};
    ScoringRule rule = {1, 0, 0};
    Result result[3];

    evaluate_serial(answers, 3, key, rule, result);

    assert(result[0].correct == 4);
    assert(result[0].wrong == 0);
    assert(result[0].blank == 1);
    assert(result[0].score == 4);

    assert(result[1].correct == 2);
    assert(result[1].wrong == 2);
    assert(result[1].blank == 1);
    assert(result[1].score == 2);

    assert(result[2].correct == 2);
    assert(result[2].wrong == 0);
    assert(result[2].blank == 3);
    assert(result[2].score == 2);
}

int main() {
    // Aquí se ejecutarán las pruebas de GTest si se configura así.
    // Para este ejercicio, solo se requiere la estructura.
    return 0;
}