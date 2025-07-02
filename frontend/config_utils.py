import json

def load_scoring_config():
    try:
        with open("data/scoring.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
          "chunk_size": 0,
          "scoring": {
            "correct": 20.0,
            "wrong": -1.125,
            "blank": 0.0
          }
        }