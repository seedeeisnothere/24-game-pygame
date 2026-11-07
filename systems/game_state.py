from systems.inventory import Inventory, load_items

BASE_MAX_HP = 5
BASE_DAMAGE = 1
HEAL_AMOUNT = 2
STARTING_POTIONS = 3
STARTING_ITEMS = ["sharp_blade", "heart_charm"]


class GameState:

    def __init__(self, items=None):
        self.inventory = Inventory(items if items is not None else load_items())
        self.lost_hp = 0
        self.potions = STARTING_POTIONS
        for item_id in STARTING_ITEMS:
            self.inventory.add(item_id)

    @property
    def max_hp(self):
        return BASE_MAX_HP + self.inventory.total("max_hp")

    @property
    def hp(self):
        return max(0, self.max_hp - self.lost_hp)

    def set_hp(self, value):
        self.lost_hp = max(0, self.max_hp - value)

    @property
    def damage_bonus(self):
        return self.inventory.total("damage")

    @property
    def base_damage(self):
        return BASE_DAMAGE + self.damage_bonus