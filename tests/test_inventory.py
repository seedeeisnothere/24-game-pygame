import unittest

from systems.game_state import BASE_DAMAGE, BASE_MAX_HP, GameState
from systems.inventory import Inventory, load_items

# Small fake item list used by these tests
ITEMS = {
    "a": {"id": "a", "name": "A", "desc": "", "effects": {"damage": 1}},
    "b": {"id": "b", "name": "B", "desc": "", "effects": {"max_hp": 2}},
    "c": {"id": "c", "name": "C", "desc": "", "effects": {"damage": 2, "max_hp": 1}},
    "d": {"id": "d", "name": "D", "desc": "", "effects": {"max_hp": 4}},
}


# Tests for owning and equipping items
class TestInventory(unittest.TestCase):
    # Make an inventory that owns every test item
    def make(self):
        inventory = Inventory(ITEMS)
        for item_id in ITEMS:
            inventory.add(item_id)
        return inventory

    # Can't add the same item twice or an unknown item
    def test_add_ignores_duplicates_and_unknown(self):
        inventory = Inventory(ITEMS)
        self.assertTrue(inventory.add("a"))
        self.assertFalse(inventory.add("a"))
        self.assertFalse(inventory.add("nope"))

    # Can't equip an item you don't own
    def test_cannot_equip_item_not_owned(self):
        self.assertFalse(Inventory(ITEMS).equip("a"))

    # Only 3 items can be equipped at once
    def test_slot_limit_is_three(self):
        inventory = self.make()
        self.assertTrue(inventory.equip("a"))
        self.assertTrue(inventory.equip("b"))
        self.assertTrue(inventory.equip("c"))
        self.assertFalse(inventory.equip("d"))            # slots are full

    # The same item can't fill two slots
    def test_cannot_equip_same_item_twice(self):
        inventory = self.make()
        inventory.equip("a")
        self.assertFalse(inventory.equip("a"))

    # Unequipping frees the slot and removes its stats
    def test_unequip_frees_slot_and_removes_bonus(self):
        inventory = self.make()
        for item_id in "abc":
            inventory.equip(item_id)
        self.assertEqual(inventory.total("damage"), 3)
        self.assertEqual(inventory.total("max_hp"), 3)
        inventory.unequip(2)                              # take off c
        self.assertEqual(inventory.total("damage"), 1)
        self.assertTrue(inventory.equip("d"))             # now there is a free slot


# Tests for player stats and coins
class TestGameState(unittest.TestCase):
    # Items in the data file only use known effects
    def test_item_file_is_valid(self):
        items = load_items()
        self.assertTrue(items)
        for item in items.values():
            self.assertTrue(set(item["effects"]) <= {"damage", "max_hp"}, item["id"])

    # Max HP and damage include equipped item bonuses
    def test_stats_follow_equipment(self):
        state = GameState(ITEMS)
        state.inventory.owned = []
        state.inventory.equipped = [None] * 3
        self.assertEqual(state.max_hp, BASE_MAX_HP)
        self.assertEqual(state.base_damage, BASE_DAMAGE)
        state.inventory.add("b"); state.inventory.equip("b")
        state.inventory.add("a"); state.inventory.equip("a")
        self.assertEqual(state.max_hp, BASE_MAX_HP + 2)
        self.assertEqual(state.base_damage, BASE_DAMAGE + 1)
        self.assertEqual(state.hp, state.max_hp)

    # Spending more coins than you have fails and changes nothing
    def test_coins(self):
        state = GameState(ITEMS)
        state.add_coins(5)
        self.assertFalse(state.spend_coins(6))
        self.assertEqual(state.coins, 5)       # not enough = nothing taken
        self.assertTrue(state.spend_coins(5))
        self.assertEqual(state.coins, 0)


if __name__ == "__main__":
    unittest.main()