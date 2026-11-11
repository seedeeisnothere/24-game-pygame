import json
import random

PUZZLE_PATH = "data/puzzles.json"
DEFAULT_DIFFICULTY = "easy"


# Load the list of puzzles for one difficulty from JSON.
def load_puzzles(difficulty=DEFAULT_DIFFICULTY, path=PUZZLE_PATH):
    with open(path, "r") as file:
        return json.load(file)[difficulty]


# Pick a random puzzle, avoiding the last one if possible.
def random_puzzle(puzzles, last=None):
    # If every puzzle equals `last`, fall back to the full list
    choices = [p for p in puzzles if p != last] or puzzles
    return random.choice(choices)
