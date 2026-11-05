from systems.inventory import Inventory, load_items

BASE_MAX_HP = 5
BASE_DAMAGE = 1
STARTING_ITEMS = ["sharp_blade", "heart_charm"]   # TODO: ชั่วคราวไว้ทดสอบเมนู ลบออกเมื่อมีร้านค้า


class GameState:
    """ข้อมูลที่ต้องจำข้ามฉาก (ค่าสถานะผู้เล่น + ไอเทม)"""

    def __init__(self, items=None):
        self.inventory = Inventory(items if items is not None else load_items())
        for item_id in STARTING_ITEMS:
            self.inventory.add(item_id)

    @property
    def max_hp(self):
        return BASE_MAX_HP + self.inventory.total("max_hp")

    @property
    def hp(self):
        return self.max_hp

    @property
    def damage_bonus(self):
        return self.inventory.total("damage")

    @property
    def base_damage(self):
        return BASE_DAMAGE + self.damage_bonus