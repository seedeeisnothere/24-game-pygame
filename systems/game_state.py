from systems.inventory import Inventory, load_items
from systems.quest import Quest

BASE_MAX_HP = 5
BASE_DAMAGE = 1
HEAL_AMOUNT = 2
STARTING_POTIONS = 3
STARTING_SKIPS = 1             # skip tickets: swap a 24 puzzle you're stuck on
STARTING_ITEMS = []
STARTING_COINS = 0
FUEL_NEEDED = 3                 # fuel pieces to fix the ship


# Player progress kept between scenes: HP, potions, skips, coins and inventory.
class GameState:
    def __init__(self, items=None):
        self.inventory = Inventory(items if items is not None else load_items())
        # Store damage taken, not current HP, so max HP changes keep it correct
        self.lost_hp = 0
        self.potions = STARTING_POTIONS
        self.skips = STARTING_SKIPS
        self.coins = STARTING_COINS
        # Picked up near the wreck at the start. Kept out of the inventory.
        self.has_gun = False
        # The quest being worked on (shown bottom-right), and ids of turned-in ones
        self.quest = None
        self.finished_quests = set()
        # Story events that happened, e.g. "forest_boss_appeared"
        self.flags = set()
        self.fuel = 0
        for item_id in STARTING_ITEMS:
            self.inventory.add(item_id)

    def start_quest(self, quest_id):
        self.quest = Quest(quest_id)

    # True while this quest is taken but not turned in yet.
    def quest_active(self, quest_id):
        return self.quest is not None and self.quest.id == quest_id

    # Called after every won battle with the enemy's kind (e.g. "slime").
    def record_kill(self, kind):
        if self.quest:
            self.quest.record_kill(kind)

    # Hand in the current quest: it's removed from the tracker.
    def finish_quest(self):
        if self.quest:
            self.finished_quests.add(self.quest.id)
            self.quest = None

    # Finish the current quest (if any) and start the next one.
    def next_quest(self, quest_id):
        self.finish_quest()
        self.start_quest(quest_id)

    # True once this quest has been handed in (or replaced by the next one).
    def quest_done(self, quest_id):
        return quest_id in self.finished_quests

    # Fuel pieces are numbered, so a replayed dialogue can't give one twice.
    def give_fuel(self, piece):
        self.fuel = max(self.fuel, piece)

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
