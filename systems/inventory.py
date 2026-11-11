import json

ITEM_PATH = "data/item.json"
SLOT_COUNT = 3


# Read every item in the game from JSON. Returns {item id: item data}.
def load_items(path=ITEM_PATH):
    with open(path, "r", encoding="utf-8") as file:
        return {item["id"]: item for item in json.load(file)["items"]}


# Items the player owns, and which ones are equipped in a few slots.
class Inventory:
    def __init__(self, items, slot_count=SLOT_COUNT):
        self.items = items
        self.owned = []
        # Each slot holds an item id, or None if empty
        self.equipped = [None] * slot_count

    # Add an item. Returns False if it doesn't exist or is already owned.
    def add(self, item_id):
        if item_id not in self.items or item_id in self.owned:
            return False
        self.owned.append(item_id)
        return True

    # Put an owned item in the first empty slot. False if it can't.
    def equip(self, item_id):
        if item_id not in self.owned or item_id in self.equipped:
            return False
        for slot, current in enumerate(self.equipped):
            if current is None:
                self.equipped[slot] = item_id
                return True
        return False

    def unequip(self, slot):
        self.equipped[slot] = None

    # Add up one effect (e.g. "damage") across all equipped items.
    def total(self, effect):
        return sum(self.items[item_id]["effects"].get(effect, 0)
                   for item_id in self.equipped if item_id)
