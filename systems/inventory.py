import json

ITEM_PATH = "data/item.json"
SLOT_COUNT = 3


def load_items(path=ITEM_PATH):
    """อ่านรายการไอเทมทั้งหมดในเกม -> {id: ข้อมูลไอเทม}"""
    with open(path, "r", encoding="utf-8") as file:
        return {item["id"]: item for item in json.load(file)["items"]}


class Inventory:

    def __init__(self, items, slot_count=SLOT_COUNT):
        self.items = items
        self.owned = []
        self.equipped = [None] * slot_count

    def add(self, item_id):
        if item_id not in self.items or item_id in self.owned:
            return False
        self.owned.append(item_id)
        return True

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

    def total(self, effect):
        return sum(self.items[item_id]["effects"].get(effect, 0)
                   for item_id in self.equipped if item_id)