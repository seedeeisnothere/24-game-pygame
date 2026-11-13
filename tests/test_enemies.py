import json
import string
import unittest

# Largest wave size allowed in enemy data
MAX_ATTACKS_AT_ONCE = 3


# Checks that data/enemies.json is filled in correctly
class TestEnemyData(unittest.TestCase):
    # Load the enemy data before each test
    def setUp(self):
        with open("data/enemies.json", "r", encoding="utf-8") as file:
            self.enemies = json.load(file)["enemies"]

    # The data file has at least one enemy
    def test_there_is_at_least_one_enemy(self):
        self.assertTrue(self.enemies)

    # Every enemy has sensible stats and battle settings
    def test_every_enemy_is_valid(self):
        for enemy_id, enemy in self.enemies.items():
            low, high = enemy["coin_reward"]
            self.assertTrue(1 <= low <= high, f"{enemy_id}.coin_reward")
            battle = enemy["battle"]
            self.assertTrue(enemy["name"], enemy_id)
            self.assertGreater(enemy["hp"], 0, enemy_id)
            for key in ("attack_wait", "attack_gap"):
                low, high = battle[key]
                self.assertTrue(0 < low <= high, f"{enemy_id}.{key}")
            self.assertGreater(battle["dodge_time"], 0, enemy_id)
            sizes = battle["wave_sizes"]
            self.assertTrue(sizes, enemy_id)
            self.assertTrue(all(1 <= n <= MAX_ATTACKS_AT_ONCE for n in sizes), enemy_id)
            keys = battle["dodge_keys"]
            self.assertTrue(set(keys) <= set(string.ascii_uppercase), enemy_id)
            self.assertEqual(len(keys), len(set(keys)), enemy_id)
            self.assertGreaterEqual(len(keys), max(sizes), enemy_id)


if __name__ == "__main__":
    unittest.main()