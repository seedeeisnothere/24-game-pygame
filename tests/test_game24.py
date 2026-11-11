import unittest
from fractions import Fraction

from logic.game24 import Game24, apply_op, can_make
from logic.puzzle_bank import load_puzzles


class TestGame24(unittest.TestCase):
    def test_divide_by_zero_is_none(self):
        self.assertIsNone(apply_op(Fraction(3), "/", Fraction(0)))

    def test_can_make(self):
        self.assertTrue(can_make([2, 12, 1, 1]))
        self.assertTrue(can_make([3, 3, 8, 8]))      # 8 / (3 - 8/3)
        self.assertFalse(can_make([1, 1, 1, 1]))

    def test_play_through_solved(self):
        game = Game24([2, 12, 1, 1])
        game.click_number(0); game.click_op("*"); game.click_number(1)   # 2*12 = 24 (อยู่ช่อง 1)
        game.click_op("*"); game.click_number(2)   # 24*1
        game.click_op("*"); game.click_number(3)   # 24*1
        self.assertTrue(game.solved)

    def test_failed_and_reset(self):
        game = Game24([1, 1, 1, 1])
        game.click_number(0)
        for b in (1, 2, 3):
            game.click_op("+"); game.click_number(b)
        self.assertTrue(game.failed)
        game.reset()
        self.assertEqual(len(game.remaining()), 4)

    def test_divide_by_zero_click_is_ignored(self):
        game = Game24([5, 5, 1, 1])
        game.click_number(0); game.click_op("-"); game.click_number(1)   # 5-5 = 0 อยู่ช่อง 1
        game.click_number(2); game.click_op("/"); game.click_number(1)   # 1/0 ต้องไม่เกิดผล
        self.assertEqual(game.values[2], Fraction(1))
        self.assertEqual(game.values[1], Fraction(0))

    def test_every_bank_puzzle_is_solvable(self):
        for numbers in load_puzzles():
            self.assertTrue(can_make(numbers), numbers)


if __name__ == "__main__":
    unittest.main()