import unittest
from fractions import Fraction

from logic.game24 import Game24, apply_op, can_make
from logic.puzzle_bank import load_puzzles


# Tests for the 24 solver and the click-based puzzle
class TestGame24(unittest.TestCase):
    # Dividing by zero gives None instead of crashing
    def test_divide_by_zero_is_none(self):
        self.assertIsNone(apply_op(Fraction(3), "/", Fraction(0)))

    # Solver finds answers, including ones that need fractions
    def test_can_make(self):
        self.assertTrue(can_make([2, 12, 1, 1]))
        self.assertTrue(can_make([3, 3, 8, 8]))      # 8 / (3 - 8/3)
        self.assertFalse(can_make([1, 1, 1, 1]))

    # Clicking through a correct answer marks the puzzle solved
    def test_play_through_solved(self):
        game = Game24([2, 12, 1, 1])
        game.click_number(0); game.click_op("*"); game.click_number(1)   # 2*12 = 24 (in slot 1)
        game.click_op("*"); game.click_number(2)   # 24*1
        game.click_op("*"); game.click_number(3)   # 24*1
        self.assertTrue(game.solved)

    # Wrong final number means failed; reset restores all 4 numbers
    def test_failed_and_reset(self):
        game = Game24([1, 1, 1, 1])
        game.click_number(0)
        for b in (1, 2, 3):
            game.click_op("+"); game.click_number(b)
        self.assertTrue(game.failed)
        game.reset()
        self.assertEqual(len(game.remaining()), 4)

    # Clicking a divide by zero leaves the numbers unchanged
    def test_divide_by_zero_click_is_ignored(self):
        game = Game24([5, 5, 1, 1])
        game.click_number(0); game.click_op("-"); game.click_number(1)   # 5-5 = 0 (in slot 1)
        game.click_number(2); game.click_op("/"); game.click_number(1)   # 1/0 should do nothing
        self.assertEqual(game.values[2], Fraction(1))
        self.assertEqual(game.values[1], Fraction(0))

    # Clicking the selected operator again unselects it; another one switches
    def test_click_same_op_unselects(self):
        game = Game24([1, 2, 3, 4])
        game.click_number(0)
        game.click_op("+")
        game.click_op("+")
        self.assertIsNone(game.op)
        game.click_op("+")
        game.click_op("*")
        self.assertEqual(game.op, "*")

    # Every puzzle in data/puzzles.json has a solution
    def test_every_bank_puzzle_is_solvable(self):
        for numbers in load_puzzles():
            self.assertTrue(can_make(numbers), numbers)


if __name__ == "__main__":
    unittest.main()