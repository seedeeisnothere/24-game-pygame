from systems.inventory import Inventory, load_items

BASE_MAX_HP = 5
BASE_DAMAGE = 1
HEAL_AMOUNT = 2
STARTING_POTIONS = 3
STARTING_ITEMS = []
STARTING_COINS = 0


# Player progress kept between scenes: HP, potions, coins and inventory.
class GameState:
    def __init__(self, items=None):
        self.inventory = Inventory(items if items is not None else load_items())
        # Store damage taken, not current HP, so max HP changes keep it correct
        self.lost_hp = 0
        self.potions = STARTING_POTIONS
        self.coins = STARTING_COINS
        for item_id in STARTING_ITEMS:
            self.inventory.add(item_id)

    def add_coins(self, amount):
        self.coins += amount

    # Pay coins. Returns False (and pays nothing) if there aren't enough.
    def spend_coins(self, amount):
        if amount > self.coins:
            return False
        self.coins -= amount
        return True

    # Base max HP plus bonuses from equipped items.
    @property
    def max_hp(self):
        return BASE_MAX_HP + self.inventory.total("max_hp")

    @property
    def hp(self):
        return max(0, self.max_hp - self.lost_hp)

    # Set current HP by working out how much has been lost.
    def set_hp(self, value):
        self.lost_hp = max(0, self.max_hp - value)

    # Extra damage from equipped items.
    @property
    def damage_bonus(self):
        return self.inventory.total("damage")

    @property
    def base_damage(self):
        return BASE_DAMAGE + self.damage_bonus
