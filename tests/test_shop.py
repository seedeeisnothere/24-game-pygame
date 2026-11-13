import unittest

from systems.game_state import STARTING_POTIONS, STARTING_SKIPS, GameState
from systems.shop import CONSUMABLES, Shop, load_shops

# Fake items and shop stock used by these tests
ITEMS = {
    "axe": {"id": "axe", "name": "Axe", "desc": "", "effects": {"damage": 2}},
}
STOCK = [
    {"item": "potion", "price": 3},
    {"item": "axe", "price": 10},
    {"item": "skip", "price": 4},
]


# Tests for buying from a shop
class TestShop(unittest.TestCase):
    # Make a test shop and a game state with the given coins
    def make(self, coins):
        state = GameState(ITEMS)
        state.coins = coins
        return Shop("Test", STOCK), state

    # Buying takes the price and adds the item
    def test_buy_item_spends_coins_and_adds_to_inventory(self):
        shop, state = self.make(12)
        self.assertEqual(shop.buy(state, STOCK[1]), "bought")
        self.assertEqual(state.coins, 2)
        self.assertIn("axe", state.inventory.owned)

    # Too few coins: nothing is bought or spent
    def test_not_enough_coins_changes_nothing(self):
        shop, state = self.make(5)
        self.assertEqual(shop.buy(state, STOCK[1]), "no_coins")
        self.assertEqual(state.coins, 5)
        self.assertNotIn("axe", state.inventory.owned)

    # Equipment sells out after one purchase
    def test_equipment_can_only_be_bought_once(self):
        shop, state = self.make(30)
        shop.buy(state, STOCK[1])
        self.assertTrue(shop.is_sold_out(state, STOCK[1]))
        self.assertEqual(shop.buy(state, STOCK[1]), "owned")
        self.assertEqual(state.coins, 20)

    # Potions never sell out
    def test_potions_can_be_bought_repeatedly(self):
        shop, state = self.make(6)
        self.assertEqual(shop.buy(state, STOCK[0]), "bought")
        self.assertEqual(shop.buy(state, STOCK[0]), "bought")
        self.assertEqual(state.potions, STARTING_POTIONS + 2)
        self.assertFalse(shop.is_sold_out(state, STOCK[0]))

    # Skip tickets never sell out and add to the skip count
    def test_skip_tickets_can_be_bought_repeatedly(self):
        shop, state = self.make(8)
        self.assertEqual(shop.buy(state, STOCK[2]), "bought")
        self.assertEqual(shop.buy(state, STOCK[2]), "bought")
        self.assertEqual(state.skips, STARTING_SKIPS + 2)
        self.assertEqual(state.coins, 0)
        self.assertFalse(shop.is_sold_out(state, STOCK[2]))

    # Shop data only lists real items with positive prices
    def test_shop_data_only_sells_real_items(self):
        items = GameState().inventory.items
        for shop in load_shops().values():
            for entry in shop["stock"]:
                self.assertTrue(entry["item"] in CONSUMABLES or entry["item"] in items, entry)
                self.assertGreater(entry["price"], 0)


if __name__ == "__main__":
    unittest.main()
