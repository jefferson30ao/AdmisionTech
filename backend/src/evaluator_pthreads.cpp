#include <pthread.h>
#include <vector>
#include <numeric>
#include "evaluator.hpp"
#include <thread> // Para std::thread::hardware_concurrency()

namespace exam {

// Estructura para pasar datos a cada hilo
struct ThreadData {
    const int8_t* answers;
    size_t num_students;
    const int8_t* key;
    size_t num_questions;
    ScoringRule rule;
    Result* out;
    size_t start_student;
    size_t end_student;
};

// Función worker para cada hilo
void* worker(void* arg) {
    ThreadData* data = static_cast<ThreadData*>(arg);

    for (size_t i = data->start_student; i < data->end_student; ++i) {
        double score = 0.0;
        uint32_t correct = 0;
        uint32_t wrong = 0;
        uint32_t blank = 0;

        for (size_t j = 0; j < data->num_questions; ++j) {
            int8_t answer = data->answers[i * data->num_questions + j];
            if (answer == -1) {
                blank++;
            } else if (answer == data->key[j]) {
                correct++;
                score += data->rule.correct;
            } else if (answer >= 0 && answer <= 3) {
                wrong++;
                score += data->rule.wrong;
            }
        }

        data->out[i].score = score;
        data->out[i].correct = correct;
        data->out[i].wrong = wrong;
        data->out[i].blank = blank;
    }
    return NULL;
}

// Función principal para la evaluación con Pthreads
void evaluate_pthreads(const int8_t* answers, size_t num_students, const int8_t* key, size_t num_questions, ScoringRule rule, Result* out) {
    unsigned int num_threads_supported = std::thread::hardware_concurrency();
    size_t num_threads = (num_threads_supported > 0) ? num_threads_supported : 1;
    if (num_students < num_threads) {
        num_threads = num_students;
    }

    std::vector<pthread_t> threads(num_threads);
    std::vector<ThreadData> thread_data(num_threads);

    size_t students_per_thread = num_students / num_threads;
    size_t remaining_students = num_students % num_threads;

    size_t current_student_idx = 0;
    for (size_t i = 0; i < num_threads; ++i) {
        thread_data[i].answers = answers;
        thread_data[i].num_students = num_students; // No se usa directamente en el worker loop, pero se mantiene por consistencia
        thread_data[i].key = key;
        thread_data[i].num_questions = num_questions;
        thread_data[i].rule = rule;
        thread_data[i].out = out;
        thread_data[i].start_student = current_student_idx;
        
        size_t end_idx = current_student_idx + students_per_thread;
        if (i < remaining_students) {
            end_idx++; // Distribuir los estudiantes restantes
        }
        thread_data[i].end_student = end_idx;
        current_student_idx = end_idx;

        pthread_create(&threads[i], NULL, worker, &thread_data[i]);
    }

    // Esperar a que todos los hilos terminen
    for (size_t i = 0; i < num_threads; ++i) {
        pthread_join(threads[i], NULL);
    }
}

} // namespace exam