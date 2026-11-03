import json
import random

PUZZLE_PATH = "data/puzzles.json"
DEFAULT_DIFFICULTY = "easy"


def load_puzzles(difficulty=DEFAULT_DIFFICULTY, path=PUZZLE_PATH):
    with open(path, "r") as file:
        return json.load(file)[difficulty]


def random_puzzle(puzzles, last=None):
    choices = [p for p in puzzles if p != last] or puzzles
    return random.choice(choices)