import time
import pandas as pd
import pyevalcore
import numpy as np

def create_sample_data(num_students, num_questions):
    answers = np.random.randint(0, 4, size=(num_students, num_questions), dtype=np.int8)
    key = np.random.randint(0, 4, size=num_questions, dtype=np.int8)
    return answers, key

def benchmark(modes, num_students=1000, num_questions=100):
    results = []
    answers, key = create_sample_data(num_students, num_questions)
    scoring_rule = pyevalcore.ScoringRule()
    scoring_rule.correct = 20
    scoring_rule.wrong = -1.125
    scoring_rule.blank = 0

    for mode in modes:
        start_time = time.perf_counter()
        if mode == "serial":
            py_results = pyevalcore.run_serial(answers, key, scoring_rule)
        elif mode == "openmp":
            py_results = pyevalcore.run_openmp(answers, key, scoring_rule)
        elif mode == "cuda":
            py_results = pyevalcore.run_cuda(answers, key, scoring_rule)
        else:
            raise ValueError(f"Unknown mode: {mode}")
        end_time = time.perf_counter()
        results.append({"mode": mode, "time": end_time - start_time})

    df = pd.DataFrame(results)
    df.to_csv("benchmark.csv", index=False)

if __name__ == "__main__":
    modes = ["serial", "openmp", "cuda"]  # Modes to benchmark
    benchmark(modes)