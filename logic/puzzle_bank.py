import json
import random

PUZZLE_PATH = "data/puzzles.json"


def load_puzzles(path=PUZZLE_PATH):
    with open(path, "r") as file:
        return json.load(file)["puzzles"]


def random_puzzle(puzzles, last=None):
    choices = [p for p in puzzles if p != last] or puzzles
    return random.choice(choices)