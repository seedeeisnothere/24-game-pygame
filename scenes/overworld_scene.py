import math
import random
import pygame
from settings import *
from systems.tilemap import *
from entities.player import *
from entities.enemy import Enemy, EnemyEncounter, EnemySpawner, SlimeSprite, MonsterSprite
from systems.settings_panel import SettingsPanel
from scenes.scene import Scene
from scenes.battle_scene import BattleScene
from entities.npc import NPC
from systems.dialogue import DialogueSystem
from systems.status_menu import StatusMenu
from entities.gate import Gate
from systems.hud import (MenuHint, CoinCounter, HealthBar, ObjectiveTracker, FuelCounter,
                         COIN_ICON_HEIGHT, FUEL_ROW_GAP)
from systems.game_state import FUEL_NEEDED
from systems.minimap import Minimap
from systems.shop import ShopMenu
from entities.wreck import Wreck
from entities.gun import GunPickup
from types import SimpleNamespace
from systems.dialogue import PLAYER_NAME
from systems.debug_skip import DEBUG_SKIP_KEY, skip_to_checkpoint  # DEBUG SKIP

WRECK_POS = (400, 2868)          # crashed ship, bottom-left of map 1
GUN_POS = (672, 2682)           # gun center, just behind the rock at tile (10, 42)
# Intro walk from the wreck to the gun: feet positions to walk through.
# Straight up first, then right along row 41 until the player touches the gun.
INTRO_WALK = [(580, 2650), (636, 2650)]
# Camera pan to the village during the intro (cue "pan_village").
PAN_TIME = 1.6                   # seconds to glide there (and the same to glide back)
PAN_HOLD = 1.2                   # seconds to look at the village
PAN_ZOOM = 0.55                  # zoom while looking (0.5 = see twice as far)
MAP1_WIDTH = 80 * 64             # map 1 is 80 tiles of 64 px
# Point to center on. x is picked so that, fully zoomed out, the right edge
# of the screen is exactly the right edge of the map (no clamping = smooth pan).
VILLAGE_VIEW = (MAP1_WIDTH - SCREEN_WIDTH / PAN_ZOOM / 2, 1560)


# The forest boss shows up mid-dialogue (cue "boss_appear").
SHAKE_TIME = 0.9                 # seconds of screen shake after the explosion
SHAKE_PX = 14                    # strongest shake offset; fades out over SHAKE_TIME
BOSS_PAN_ZOOM = 0.8              # slight zoom out while looking at the boss
QUEST_CLEAR_DELAY = 3.0          # crossed-out quests with no turn-in vanish after this
FLASH_TIME = 1.4                 # white flash when Jenny shows her true form

# Jenny waits next to the wreck once the cave boss is beaten.
JENNY_SPRITE = "assets/sprites/player/idle.png"   # same suit as John, tinted pink
JENNY_TINT = (255, 120, 185)
JENNY_BOSS_SPRITE = "assets/sprites/boss/jenny"
JENNY_FROM_WRECK = (70, -6)      # her feet, from the wreck's bottom-right corner
JENNY_TRIGGER = 230              # walk this close and the meeting starts

# Ship repair after Jenny: "Let's fix the ship!", walk over, white flash
# (the ship is fixed behind it), look at it, fade to black, EndScene.
REPAIR_FROM_WRECK = (40, -20)    # John's feet, from the wreck's bottom-right corner
REPAIR_WHITE_IN = 1.0            # seconds to fade to white
REPAIR_WHITE_HOLD = 0.6          # full white (the ship gets fixed here)
REPAIR_WHITE_OUT = 1.0           # fade back from white
REPAIR_LOOK = 1.8                # look at the fixed ship
REPAIR_BLACK_IN = 1.4            # fade to black, then the ending


# Smooth 0 -> 1 curve: slow start, slow end.
def smoothstep(t):
    return t * t * (3 - 2 * t)
BOSS_POS = (2528, 1330)          # map 1 boss, guards the stone bridge
SHOP_NPC_FEET = (3962, 1207)     # shopkeeper's feet, next to the well on the right
SHOP_NPC_SPRITE = "assets/sprites/npc/shopkeeper.png"
# Coin-farming area: the top-left dirt field (tiles 5-20 x 5-15).
FARM_ZONE = pygame.Rect(320, 300, 1024, 724)
FARM_WAVE_SIZE = (1, 2)          # min/max enemies per farm wave
FARM_RESPAWN_DISTANCE = 900      # walk this far away to respawn the farm
CRASH_FADE_TIME = 1.6            # seconds of white fade after the crash
TALK_LEAVE_REACH = 110           # walk farther than this to close talk/shop
TILE_PX = TILE * SCALE           # size of one tile on screen (64 px)

# Villagers on map 1: (sprite number, tile col, tile row).
# Sprite is assets/sprites/npc/NPC_<number>.png, dialogue id is "npc_<number>"
# in data/dialogue.json. Each one stands with its feet on that tile.
VILLAGERS = [
    (5, 16, 26),
    (6, 35, 39),
    (7, 71, 37),
    (10, 51, 30),
    (12, 64, 8),
]
# Special names; every other villager is just called "Villager".
VILLAGER_NAMES = {10: "Village Headman"}
# Villagers shown on the minimap as a blue diamond.
MINIMAP_VILLAGERS = {10}
# The headman drives the story. His dialogue ids in data/dialogue.json:
#   npc_10               first talk, gives the slime quest
#   npc_10_waiting       slimes not all killed yet
#   npc_10_complete      slimes done: fuel 1, the Crimson Warden appears
#   npc_10_boss_waiting  Crimson Warden not beaten yet
#   npc_10_forest_done   Warden beaten: fuel 2, gives the cave quest
#   npc_10_cave_waiting  cave monster not beaten yet
#   npc_10_cave_done     cave monster beaten: fuel 3, "someone is at your ship"
#   npc_10_after         every talk after that
HEADMAN = 10
SLIME_QUEST = "slime_hunt"


# World rectangle covering tiles, counted from the top-left tile (0, 0).
def tile_rect(col, row, cols=1, rows=1):
    return pygame.Rect(col * TILE_PX, row * TILE_PX, cols * TILE_PX, rows * TILE_PX)


# Center point of a tile; col 39.5 means halfway between two tiles.
def tile_point(col, row):
    return (round((col + 0.5) * TILE_PX), round((row + 0.5) * TILE_PX))


# Settings for each map:
#   spawn   = player's feet position on first visit (None = next to wreck)
#   boss    = boss top-left (as if 64 x 87); beating it opens that map's gates
#   boss_sprite = folder of the boss's frame_XX.png animation
#   boss_id = the boss's entry in data/enemies.json (name, hp, battle settings)
#   boss_flag = (optional) boss stays hidden until game.state.flags has this
#   portals = list of (world area, target map, spawn there or None)
MAPS = {
    "map1": {
        "path": "data/maps/map1.json",
        "spawn": None,
        "boss": BOSS_POS,
        "boss_sprite": "assets/sprites/boss/monster_01",
        "boss_id": "boss_forest",
        # Hidden until this flag is set (by the headman's "boss_appear" cue).
        "boss_flag": "forest_boss_appeared",
        # The cave mouth tiles are solid, so the portal sticks out 8 px below.
        "portals": [(tile_rect(36, 5, 2, 1).inflate(0, 16).move(0, 8), "map2", None)],
        "minimap": {},
    },
    "map2": {
        "path": "data/maps/map2.json",
        # Bottom end of the wooden bridge.
        "spawn": tile_point(39.5, 42),
        # Boss stands mid-bridge; 87 lines its feet up with the middle of row 16.
        "boss": (40 * TILE_PX - 32, 16 * TILE_PX + 32 - 87),
        "boss_sprite": "assets/sprites/boss/monster_02",
        "boss_id": "boss_cave",
        # Hidden until the headman gives the cave quest.
        "boss_flag": "cave_boss_appeared",
        # Cave exit at the bottom leads back to the cave mouth on map 1.
        "portals": [(tile_rect(38, 45, 4, 2), "map1", tile_point(36.5, 7))],
        "minimap": {"water_layers": ["น้ำ"], "outline_solid": True},
    },
}


# A "speaker" for lines the player says to themself (all lines are "player").
def monologue(dialogue_id):
    return SimpleNamespace(name=PLAYER_NAME, portrait=None, dialogue_id=dialogue_id)


# Go to a map, reusing its scene if visited (keeps boss/gate/enemy state).
def travel(game, map_id, spawn=None):
    scene = game.overworlds.get(map_id) or OverworldScene(game, map_id)
    scene.arrive(spawn or MAPS[map_id]["spawn"])
    return scene


# The walkable world: player movement, camera, NPCs, enemies, gates, HUD.
class OverworldScene(Scene):
    def __init__(self, game, map_id="map1", from_crash=False):
        super().__init__(game)
        self.map_id = map_id
        self.music = map_id     # track names match map ids (map1, map2)
        config = MAPS[map_id]
        map_path = config["path"]
        # below = drawn under characters, above = drawn on top of them.
        self.below, self.above, gate_data = load_map(map_path)
        self.solid = load_collision(map_path)
        self.portals = config["portals"]
        self.leaving = False
        game.overworlds[map_id] = self
        self.world_width = self.below.get_width()
        self.world_height = self.below.get_height()

        walk_paths = [f"Walk{i}.png" for i in range(12)]
        self.sprite = AnimatedSprite("assets/sprites/player/idle.png", walk_paths,
                                     frame_duration_ms=WALK_FRAME_MS)
        self.wreck = Wreck(*WRECK_POS) if map_id == "map1" else None
        player_rect = self.sprite.idle_right.get_rect()
        self.player_width = player_rect.width
        self.player_height = player_rect.height
        # Hitbox is a small box at the player's feet, centered horizontally.
        self.hitbox = pygame.Rect(0, 0, HITBOX_WIDTH, HITBOX_HEIGHT)
        self.hitbox_offset_x = (self.player_width - HITBOX_WIDTH) // 2
        self.hitbox_offset_y = self.player_height - HITBOX_HEIGHT
        if config["spawn"]:
            self.place_player(config["spawn"])
        else:
            # Start just right of the wreck, feet level with its base.
            self.player_x = self.wreck.body.right + 8
            self.player_y = self.wreck.body.bottom - self.player_height
        self.cam_x = 0
        self.cam_y = 0
        self.settings_panel = SettingsPanel(game, in_game=True)
        self.menu = StatusMenu(game)
        self.shop = ShopMenu(game)

        # Farm enemies are slimes in a random color.
        def make_enemy(x, y):
            slime = SlimeSprite()
            return Enemy(x, y, sprite=slime, name=f"{slime.color} Slime", kind="slime")

        # Each map's boss has its own monster. Boss positions were set for a
        # 64 x 87 sprite, so keep the feet on that same spot.
        def make_boss(x, y):
            sprite = MonsterSprite(config["boss_sprite"], scale=3, battle_scale=6)
            w, h = sprite.idle_right.get_size()
            feet_x, feet_y = x + 64 // 2, y + 87
            return Enemy(feet_x - w // 2, feet_y - h, sprite=sprite,
                         enemy_id=config["boss_id"], kind=config["boss_id"])

        self.boss = None
        self.farm = None
        self.encounter = EnemyEncounter([])
        if config.get("boss"):
            self.boss = make_boss(*config["boss"])
            self.sync_boss()
        # Only map 1 has the coin farm.
        if map_id == "map1":
            self.farm = EnemySpawner(FARM_ZONE, make_enemy, self.solid,
                                     wave_size=FARM_WAVE_SIZE,
                                     respawn_distance=FARM_RESPAWN_DISTANCE)
        self.menu_hint = MenuHint()
        self.coin_counter = CoinCounter()
        self.fuel_counter = FuelCounter(self.coin_counter.top + COIN_ICON_HEIGHT + FUEL_ROW_GAP)
        self.health_bar = HealthBar()
        self.objective = ObjectiveTracker()
        self.minimap = Minimap(map_path, (self.world_width, self.world_height),
                               **config["minimap"])
        self.last_dt = 0.0

        self.gates = [Gate(tiles, rects) for tiles, rects in gate_data]

        self.dialogue = DialogueSystem("data/dialogue.json", (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.dialogue.cue_handler = self.play_cue
        self.dialogue.on_advance = lambda: game.play_sfx("hover")
        self.pan = None             # camera pan played by a dialogue cue
        self.shake = None           # screen shake played by a dialogue cue
        self.zoom = 1.0             # below 1 = zoomed out (used by the pan)
        self.zoom_buffer = None     # off-screen surface for drawing zoomed out
        self.npcs = []
        self.headman = None
        if map_id == "map1":
            shopkeeper = NPC("Shopkeeper", 0, 0, SHOP_NPC_SPRITE, "npc_elder_01",
                             shop_id="elder", sheet=True)
            shopkeeper.place(SHOP_NPC_FEET)
            self.npcs.append(shopkeeper)
            for number, col, row in VILLAGERS:
                name = VILLAGER_NAMES.get(number, "Villager")
                npc = NPC(name, 0, 0, f"assets/sprites/npc/NPC_{number}.png",
                          f"npc_{number}", sheet=True,
                          on_minimap=number in MINIMAP_VILLAGERS)
                # Feet at the bottom middle of the tile.
                npc.place((round((col + 0.5) * TILE_PX), (row + 1) * TILE_PX))
                self.npcs.append(npc)
                if number == HEADMAN:
                    self.headman = npc
        self.nearby_npc = None
        self.talking_npc = None
        self.talk_hint = pygame.font.Font(FONT_PATH, SMALL_FONT_SIZE).render(
            "Click / E", False, TEXT_COLOR)

        self.hitbox.topleft = (self.player_x + self.hitbox_offset_x,
                               self.player_y + self.hitbox_offset_y)
        self.update_camera()
        # White overlay that fades out after the crash intro.
        self.white = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.white.fill("#FFFFFF")
        self.crash_fade = CRASH_FADE_TIME if from_crash else 0.0

        # Gun lying behind the rock near the wreck (map 1 only).
        self.gun = GunPickup(*GUN_POS) if map_id == "map1" else None
        # Jenny (map 1 only): an NPC by the wreck, and the final boss fight.
        self.jenny = None
        self.jenny_enemy = None
        if self.wreck:
            self.jenny, self.jenny_enemy = self.make_jenny()
        # (enemy, "win"/"lose"/"flee") set by BattleScene, handled on return
        self.battle_result = None
        self.flash = 0.0            # white flash time left (Jenny's reveal)
        # Intro after the crash: "pending" -> "talk" -> "walk" -> "gun_talk" -> None
        self.intro = "pending" if from_crash else None
        self.intro_path = []
        # Ship repair after Jenny: None -> "talk" -> "walk" -> "fix" (fades)
        self.repair = None
        self.repair_path = []
        self.repair_time = 0.0
        self.black = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

    # Move the player so the center of the hitbox (the feet) is at `feet`.
    def place_player(self, feet):
        self.player_x = feet[0] - self.hitbox_offset_x - HITBOX_WIDTH // 2
        self.player_y = feet[1] - self.hitbox_offset_y - HITBOX_HEIGHT // 2
        self.hitbox.topleft = (self.player_x + self.hitbox_offset_x,
                               self.player_y + self.hitbox_offset_y)

    # Called when entering this map (first time or returning).
    def arrive(self, feet):
        self.leaving = False
        self.close_popups()
        if feet:
            self.place_player(feet)
        self.sprite.moving = False
        self.update_camera()

    def touches_npc(self):
        return any(self.hitbox.colliderect(npc.hitbox) for npc in self.npcs)

    def touches_gate(self):
        return any(gate.blocks(self.hitbox) for gate in self.gates)

    # True if the hitbox hits a wall, NPC, closed gate or the wreck.
    def blocked(self):
        return (touches_solid(self.hitbox, self.solid) or self.touches_npc() or self.touches_gate()
                or (self.wreck is not None and self.hitbox.colliderect(self.wreck.hitbox)))

    # Camera position that centers `center`, clamped to the map edges.
    # view_size is how much of the world is visible (bigger when zoomed out).
    def camera_for(self, center, view_size=(SCREEN_WIDTH, SCREEN_HEIGHT)):
        view_w, view_h = view_size
        cam_x = round(center[0] - view_w / 2)
        cam_y = round(center[1] - view_h / 2)
        return (max(0, min(cam_x, self.world_width - view_w)),
                max(0, min(cam_y, self.world_height - view_h)))

    # Center the camera on the player, clamped to the map edges.
    def update_camera(self):
        self.cam_x, self.cam_y = self.camera_for(
            (self.player_x + self.player_width // 2, self.player_y + self.player_height // 2))

    # Dialogue cues (see "cue" in data/dialogue.json). Call done() when finished.
    def play_cue(self, name, done):
        if name.startswith("fuel_"):
            # "fuel_2" = hand over fuel piece 2
            self.game.state.give_fuel(int(name.split("_")[1]))
            self.game.play_sfx("pickup")
            done()
        elif name == "jenny_reveal":
            # Boom, white flash and shake; she's in her true form when it clears.
            self.game.play_sfx("explosion")
            self.flash = FLASH_TIME
            self.game.state.flags.add("jenny_revealed")
            self.sync_jenny()
            self.shake = {"time": 0.0, "then": done}
        elif name == "pan_village":
            self.pan = {"target": VILLAGE_VIEW, "zoom": PAN_ZOOM, "time": 0.0, "done": done}
        elif name == "boss_appear" and self.boss:
            # Boom + shake, then look at the boss and come back.
            self.reveal_boss()
            self.game.play_sfx("explosion")
            pan = {"target": self.boss.rect.center, "zoom": BOSS_PAN_ZOOM, "time": 0.0, "done": done}
            self.shake = {"time": 0.0, "then": lambda: setattr(self, "pan", pan)}
        else:
            print(f"[warn] unknown dialogue cue: {name}")
            done()

    # Camera pan: glide from the player to the target while zooming out,
    # wait, then glide back and zoom in again.
    # Runs after update_camera(), so cam_x/cam_y start on the player.
    def update_pan(self, dt):
        pan = self.pan
        if pan is None:
            self.zoom = 1.0
            return
        pan["time"] += dt
        t = pan["time"]
        if t < PAN_TIME:
            k = smoothstep(t / PAN_TIME)
        elif t < PAN_TIME + PAN_HOLD:
            k = 1.0
        elif t < PAN_TIME * 2 + PAN_HOLD:
            k = 1.0 - smoothstep((t - PAN_TIME - PAN_HOLD) / PAN_TIME)
        else:
            self.pan = None
            self.zoom = 1.0
            pan["done"]()
            return
        # Blend the view center and the zoom between the player and the target.
        home_x = self.cam_x + SCREEN_WIDTH / 2
        home_y = self.cam_y + SCREEN_HEIGHT / 2
        target_x, target_y = pan["target"]
        center = (home_x + (target_x - home_x) * k, home_y + (target_y - home_y) * k)
        self.zoom = 1.0 - (1.0 - pan["zoom"]) * k
        view_size = (round(SCREEN_WIDTH / self.zoom), round(SCREEN_HEIGHT / self.zoom))
        self.cam_x, self.cam_y = self.camera_for(center, view_size)

    # True while the gun is still lying on the ground (map 1 only).
    def gun_on_ground(self):
        return self.gun is not None and not self.game.state.has_gun

    # After the first monologue: walk the player over to the gun.
    def start_intro_walk(self):
        self.intro = "walk"
        self.intro_path = list(INTRO_WALK)

    # Which way to "press" to reach the next point of the intro walk.
    # Returns (left, right, up, down).
    def intro_walk_keys(self):
        keys = self.path_keys(self.intro_path)
        if keys is None:
            # End of the path: pick the gun up even if we didn't quite touch it.
            self.pick_up_gun()
            return (False, False, False, False)
        return keys

    # Keys (left, right, up, down) that walk the feet toward the first point
    # of `path`. Points already reached are dropped; None = path finished.
    def path_keys(self, path):
        fx, fy = self.hitbox.center
        # Drop points we're already standing on (within 2 px).
        while path:
            tx, ty = path[0]
            if abs(tx - fx) > 2 or abs(ty - fy) > 2:
                return (tx < fx - 2, tx > fx + 2, ty < fy - 2, ty > fy + 2)
            path.pop(0)
        return None

    # Take the gun (it is not added to the inventory) and talk about it.
    def pick_up_gun(self):
        if not self.gun_on_ground():
            return
        self.game.state.has_gun = True
        self.game.play_sfx("pickup")
        self.intro_path = []
        self.intro = "gun_talk"
        self.dialogue.start(monologue("intro_gun"), self.end_intro)

    def end_intro(self):
        self.intro = None
        self.game.state.start_quest("find_fuel")

    def handle_events(self, events):
        if any(e.type == pygame.KEYDOWN and e.key == DEBUG_SKIP_KEY for e in events):  # DEBUG SKIP
            return skip_to_checkpoint(self)
        # No input during the crash fade or the intro walk;
        # dialogue takes all input when open.
        if self.crash_fade > 0 or self.intro == "walk" or self.repair in ("walk", "fix"):
            return
        if self.dialogue.active:
            self.dialogue.handle_events(events)
            return

        for event in events:
            # Open popups get the event first, in this priority order.
            if self.minimap.expanded:
                self.minimap.handle_event(event)
                continue
            if self.shop.is_open:
                self.shop.handle_event(event)
                continue
            if self.menu.is_open:
                self.menu.handle_event(event)
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.settings_panel.is_active():
                    self.settings_panel.close()
                else:
                    self.settings_panel.open()
            elif self.settings_panel.is_active():
                self.settings_panel.handle_event(event)
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_m:
                self.minimap.toggle()
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.menu.open()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                npc = self.clicked_npc(event.pos)
                if npc:
                    self.talk_to(npc)
                    return
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                # E talks to a nearby NPC, otherwise fights the enemy in front.
                if self.nearby_npc:
                    self.talk_to(self.nearby_npc)
                    return
                else:
                    enemy = self.encounter.enemy_in_front(self.hitbox, self.sprite.facing_right)
                    if enemy:
                        self.engage(enemy)

    # Return the NPC under the mouse, but only if it is close enough to talk.
    def clicked_npc(self, mouse_pos):
        for npc in self.npcs:
            if npc.is_clicked(mouse_pos, self.cam_x, self.cam_y) and npc.can_interact(self.hitbox):
                return npc
        return None

    # Start dialogue; shop NPCs open their shop when the dialogue ends.
    # Make a hidden boss appear (and remember it, so it stays after leaving).
    def reveal_boss(self):
        flag = MAPS[self.map_id].get("boss_flag")
        if flag:
            self.game.state.flags.add(flag)
        if self.boss not in self.encounter.enemies:
            self.encounter.enemies.append(self.boss)

    # Shake the camera, strongest at the start, then run "then".
    # Runs after the camera has been placed for this frame.
    def update_shake(self, dt):
        shake = self.shake
        if shake is None:
            return
        shake["time"] += dt
        left = 1 - shake["time"] / SHAKE_TIME
        if left <= 0:
            self.shake = None
            shake["then"]()
            return
        power = round(SHAKE_PX * left)
        self.cam_x += random.randint(-power, power)
        self.cam_y += random.randint(-power, power)

    # Quests with no one to report to clear themselves once crossed out.
    def update_quest(self, dt):
        quest = self.game.state.quest
        if quest and quest.complete and not quest.turn_in:
            quest.done_time += dt
            if quest.done_time >= QUEST_CLEAR_DELAY:
                self.game.state.finish_quest()

    def talk_to(self, npc):
        self.talking_npc = npc
        if npc is self.headman:
            self.dialogue.start(npc, *self.headman_dialogue())
            return
        if npc is self.jenny:
            # She starts the talk from further away than the usual talk range,
            # so don't let "walked away" close it.
            self.talking_npc = None
            self.dialogue.start(npc, *self.jenny_dialogue())
            return
        on_finish = (lambda: self.shop.open(npc.shop_id)) if npc.shop_id else None
        self.dialogue.start(npc, on_finish)

    # ---------------------------------------------------------------- Story
    # Order: find_fuel -> slime_hunt -> forest_boss -> cave_boss
    #        -> go_to_ship -> final_boss -> ending.

    # Pick the headman's lines for where the story is at.
    # Returns (on_finish, dialogue_id).
    def headman_dialogue(self):
        state = self.game.state
        quest = state.quest
        # (quest id, turn-in when done, lines when done, lines while working on it)
        steps = [
            (SLIME_QUEST, self.finish_slime_quest, "npc_10_complete", "npc_10_waiting"),
            ("forest_boss", self.finish_forest_quest, "npc_10_forest_done", "npc_10_boss_waiting"),
            ("cave_boss", self.finish_cave_quest, "npc_10_cave_done", "npc_10_cave_waiting"),
        ]
        for quest_id, finish, done_lines, waiting_lines in steps:
            if state.quest_active(quest_id):
                return (finish, done_lines) if quest.complete else (None, waiting_lines)
        if state.quest_done(SLIME_QUEST):
            return None, "npc_10_after"
        return self.start_slime_quest, "npc_10"

    # Slimes handed in: the Warden already appeared during the dialogue.
    def finish_slime_quest(self):
        self.game.state.give_fuel(1)
        self.reveal_boss()
        self.game.state.next_quest("forest_boss")

    # Warden handed in: the cave monster appears in the cave.
    def finish_forest_quest(self):
        self.game.state.give_fuel(2)
        self.game.state.flags.add("cave_boss_appeared")
        self.game.state.next_quest("cave_boss")

    # Cave monster handed in: Jenny is now waiting at the ship.
    def finish_cave_quest(self):
        self.game.state.give_fuel(3)
        self.game.state.flags.add("jenny_at_ship")
        self.game.state.next_quest("go_to_ship")
        self.sync_jenny()

    # Add a hidden boss once its flag is set (it may be set on another map).
    def sync_boss(self):
        if self.boss is None or self.boss.defeated or self.boss in self.encounter.enemies:
            return
        flag = MAPS[self.map_id].get("boss_flag")
        if flag is None or flag in self.game.state.flags:
            self.encounter.enemies.append(self.boss)

    # Jenny's NPC (pink John) and her boss form for the fight.
    def make_jenny(self):
        jenny = NPC("Jenny", 0, 0, JENNY_SPRITE, "jenny_meet")
        pink = jenny.frames[0].copy()
        pink.fill((70, 70, 70), special_flags=pygame.BLEND_RGB_ADD)   # lift the black
        pink.fill(JENNY_TINT, special_flags=pygame.BLEND_RGB_MULT)
        # She faces left, toward John coming from the village.
        jenny.human = [pygame.transform.flip(pink, True, False)]
        jenny.feet = (self.wreck.body.right + JENNY_FROM_WRECK[0],
                      self.wreck.body.bottom + JENNY_FROM_WRECK[1])
        boss_sprite = MonsterSprite(JENNY_BOSS_SPRITE, scale=3, battle_scale=6)
        jenny.true_form = [boss_sprite.idle_right]
        jenny.frames = jenny.human
        jenny.image = jenny.frames[0]
        jenny.place(jenny.feet)
        w, h = boss_sprite.idle_right.get_size()
        enemy = Enemy(jenny.feet[0] - w // 2, jenny.feet[1] - h, sprite=boss_sprite,
                      enemy_id="boss_final", kind="boss_final")
        return jenny, enemy

    # Show/hide Jenny and pick her look from the story flags.
    def sync_jenny(self):
        if self.jenny is None:
            return
        flags = self.game.state.flags
        here = "jenny_at_ship" in flags and not self.jenny_enemy.defeated
        if here and self.jenny not in self.npcs:
            self.npcs.append(self.jenny)
        elif not here and self.jenny in self.npcs:
            self.npcs.remove(self.jenny)
        frames = self.jenny.true_form if "jenny_revealed" in flags else self.jenny.human
        if self.jenny.frames is not frames:
            self.jenny.frames = frames
            self.jenny.image = frames[0]
            self.jenny.rect = self.jenny.image.get_rect()
            self.jenny.place(self.jenny.feet)

    # Walking up to Jenny starts the big talk on its own (only once).
    def check_jenny_meeting(self):
        if (self.jenny in self.npcs and "jenny_met" not in self.game.state.flags
                and not self.movement_locked()
                and math.dist(self.hitbox.center, self.jenny.hitbox.center) <= JENNY_TRIGGER):
            self.talk_to(self.jenny)

    # Jenny's lines: the full reveal the first time, a short one after a retreat.
    def jenny_dialogue(self):
        def fight():
            self.game.state.flags.add("jenny_met")
            if not self.game.state.quest_active("final_boss"):
                self.game.state.next_quest("final_boss")
            self.start_battle(self.jenny_enemy)
        first = "jenny_met" not in self.game.state.flags
        return fight, "jenny_meet" if first else "jenny_again"

    # Bosses say their lines the first time they catch you, then the fight starts.
    def engage(self, enemy):
        flag = f"{enemy.enemy_id}_intro_seen"
        if enemy.intro_dialogue and flag not in self.game.state.flags:
            def fight():
                self.game.state.flags.add(flag)
                self.start_battle(enemy)
            speaker = SimpleNamespace(name=enemy.name, portrait=None,
                                      dialogue_id=enemy.intro_dialogue)
            self.dialogue.start(speaker, fight)
            return
        self.start_battle(enemy)

    # Back from a battle: story lines after a boss, the ending after Jenny.
    def after_battle(self):
        enemy, result = self.battle_result
        self.battle_result = None
        if result != "win":
            return
        if enemy is self.jenny_enemy:
            self.sync_jenny()
            self.dialogue.start(monologue("jenny_outro"), self.start_repair)
        elif enemy.outro_dialogue:
            self.dialogue.start(monologue(enemy.outro_dialogue))

    # Jenny is gone: "Let's fix the ship!", then walk over to it.
    def start_repair(self):
        self.close_popups()
        self.repair = "talk"
        self.dialogue.start(monologue("ship_fix"), self.start_repair_walk)

    # Walk to the ship's right side: line up vertically first, then step in.
    def start_repair_walk(self):
        body = self.wreck.body
        target = (body.right + REPAIR_FROM_WRECK[0], body.bottom + REPAIR_FROM_WRECK[1])
        self.repair = "walk"
        self.repair_path = [(self.hitbox.centerx, target[1]), target]

    # Repair fades: white in, fix the ship, white out, look, black in, ending.
    def update_repair(self, dt):
        if self.repair != "fix":
            return
        before = self.repair_time
        self.repair_time += dt
        fix_at = REPAIR_WHITE_IN + REPAIR_WHITE_HOLD / 2
        if before < fix_at <= self.repair_time:
            self.wreck.fix()
        end = (REPAIR_WHITE_IN + REPAIR_WHITE_HOLD + REPAIR_WHITE_OUT
               + REPAIR_LOOK + REPAIR_BLACK_IN)
        if self.repair_time >= end:
            self.play_ending()

    # (white alpha, black alpha) for the repair fades, 0-255.
    def repair_overlay(self):
        if self.repair != "fix":
            return 0, 0
        t = self.repair_time
        white_out = REPAIR_WHITE_IN + REPAIR_WHITE_HOLD
        black_in = white_out + REPAIR_WHITE_OUT + REPAIR_LOOK
        if t < REPAIR_WHITE_IN:
            white = t / REPAIR_WHITE_IN
        elif t < white_out:
            white = 1.0
        else:
            white = 1.0 - min((t - white_out) / REPAIR_WHITE_OUT, 1.0)
        black = min(max((t - black_in) / REPAIR_BLACK_IN, 0.0), 1.0)
        return round(255 * smoothstep(white)), round(255 * smoothstep(black))

    # Screen is already black: cut straight to the ending (it fades in itself).
    def play_ending(self):
        from scenes.end_scene import EndScene
        self.close_popups()
        self.repair = None
        self.game.update_walk_sfx(False)
        self.game.scene = EndScene(self.game, fade_in=True)
        self.game.play_scene_music()

    # Give the quest and fill the farm with a fresh wave of quest slimes.
    def start_slime_quest(self):
        self.game.state.next_quest(SLIME_QUEST)
        if self.farm is None:
            return
        self.update_farm_size()
        # Replace whatever farm slimes are there with the quest wave.
        self.encounter.enemies = [e for e in self.encounter.enemies if e is self.boss]
        self.encounter.enemies += self.farm.spawn_wave()

    def movement_locked(self):
        return (self.dialogue.active or self.shop.is_open or self.menu.is_open
                or self.intro is not None or self.repair is not None)

    def close_popups(self):
        self.dialogue.cancel()
        self.pan = None
        self.shake = None
        self.zoom = 1.0
        self.shop.close()
        self.menu.close()
        self.minimap.close()
        self.settings_panel.close()
        self.talking_npc = None

    # Close the dialogue/shop if the player walks away from the NPC.
    def leave_npc_if_far(self):
        npc = self.talking_npc
        if not npc or not (self.dialogue.active or self.shop.is_open):
            self.talking_npc = None
            return
        if not npc.can_interact(self.hitbox, reach=TALK_LEAVE_REACH):
            self.dialogue.cancel()
            self.shop.close()
            self.talking_npc = None

    # If the player steps on a portal, switch to the target map (once).
    def check_portals(self):
        if self.leaving:
            return
        for area, target, spawn in self.portals:
            if self.hitbox.colliderect(area):
                self.leaving = True
                self.close_popups()
                self.game.update_walk_sfx(False)
                self.game.change_scene(lambda: travel(self.game, target, spawn))
                return

    # While the slime quest is running, waves are exactly the slimes still
    # needed (5 at the start); otherwise the usual random 1-2.
    def update_farm_size(self):
        quest = self.game.state.quest
        if quest and quest.id == SLIME_QUEST and not quest.complete:
            self.farm.wave_size = (quest.remaining, quest.remaining)
        else:
            self.farm.wave_size = FARM_WAVE_SIZE

    def update_farm(self):
        if self.farm is None:
            return
        self.update_farm_size()
        new = self.farm.update(self.hitbox.center)
        if new:
            # Drop defeated farm enemies (keep the boss) and add the new wave.
            self.encounter.enemies = [e for e in self.encounter.enemies
                                      if e is self.boss or not e.defeated] + new

    def start_battle(self, enemy):
        self.close_popups()
        self.game.change_scene(lambda: BattleScene(self.game, enemy, self))

    def update(self, dt):
        self.last_dt = dt
        # Settings panel open = paused: only the panel updates.
        self.settings_panel.update(dt, pygame.mouse.get_pos())
        if self.settings_panel.is_active():
            self.sprite.moving = False
            return

        if self.wreck:
            self.wreck.update(dt)
        for npc in self.npcs:
            npc.update(dt)
        self.minimap.update(dt)
        # During the crash fade the player stands still.
        if self.crash_fade > 0:
            self.crash_fade = max(0.0, self.crash_fade - dt)
            self.sprite.moving = False
            self.sprite.update(dt)
            return

        # Popups don't pause the world, but they stop the player moving.
        self.shop.update(dt)
        self.menu.update(dt)

        for gate in self.gates:
            gate.open = self.boss is not None and self.boss.defeated

        # Intro just started: the player talks to themself first.
        if self.intro == "pending":
            self.intro = "talk"
            self.dialogue.start(monologue("intro_wake"), self.start_intro_walk)

        keys = pygame.key.get_pressed()
        left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        up = keys[pygame.K_UP] or keys[pygame.K_w]
        down = keys[pygame.K_DOWN] or keys[pygame.K_s]
        if self.movement_locked() or self.leaving:
            left = right = up = down = False
        # During the intro walk the game "presses the keys" for the player.
        if self.intro == "walk":
            left, right, up, down = self.intro_walk_keys()
        elif self.repair == "walk":
            keys = self.path_keys(self.repair_path)
            if keys is None:
                # Arrived: face the ship and start the fades.
                self.repair = "fix"
                self.repair_time = 0.0
                self.sprite.facing_right = False
                keys = (False, False, False, False)
            left, right, up, down = keys

        if right and not left:
            self.sprite.facing_right = True
        elif left and not right:
            self.sprite.facing_right = False

        # Booleans subtract to -1, 0 or 1.
        dx = right - left
        dy = down - up
        step = WALK_SPEED
        # Slow down diagonals so they aren't faster than straight moves.
        if dx != 0 and dy != 0:
            step = WALK_SPEED * 3 // 4

        old_x = self.player_x
        old_y = self.player_y

        # Move X and Y separately so the player can slide along walls.
        self.player_x += dx * step
        self.player_x = max(0, min(self.player_x, self.world_width - self.player_width))
        self.hitbox.topleft = (self.player_x + self.hitbox_offset_x,
                               self.player_y + self.hitbox_offset_y)
        if self.blocked():
            self.player_x = old_x

        self.player_y += dy * step
        self.player_y = max(0, min(self.player_y, self.world_height - self.player_height))
        self.hitbox.topleft = (self.player_x + self.hitbox_offset_x,
                               self.player_y + self.hitbox_offset_y)
        if self.blocked():
            self.player_y = old_y

        # Sync the hitbox with the final position (after any undo).
        self.hitbox.topleft = (self.player_x + self.hitbox_offset_x,
                               self.player_y + self.hitbox_offset_y)

        self.sprite.moving = self.player_x != old_x or self.player_y != old_y
        # Stuck during the intro walk (shouldn't happen): skip to the next point.
        if self.intro == "walk" and not self.sprite.moving and self.intro_path:
            self.intro_path.pop(0)
        if self.repair == "walk" and not self.sprite.moving and self.repair_path:
            self.repair_path.pop(0)
        self.game.update_walk_sfx(self.sprite.moving)
        self.sprite.update(dt)

        # Walking into the gun picks it up.
        if self.gun_on_ground() and self.gun.touches(self.hitbox):
            self.pick_up_gun()

        # Story things that can change while away (other map, battle).
        self.sync_boss()
        self.sync_jenny()
        if self.battle_result and not self.dialogue.active:
            self.after_battle()
        self.check_jenny_meeting()
        self.flash = max(0.0, self.flash - dt)
        self.update_repair(dt)

        # An enemy that catches the player starts a battle.
        # Enemies hold still during dialogue, shops and menus.
        self.update_farm()
        if self.movement_locked() or self.leaving:
            self.encounter.animate(dt)
        else:
            enemy = self.encounter.update(dt, self.hitbox, self.solid)
            if enemy:
                self.engage(enemy)

        self.update_camera()
        self.update_pan(dt)
        self.update_shake(dt)
        self.update_quest(dt)
        self.leave_npc_if_far()
        self.check_portals()

        self.nearby_npc = None
        for npc in self.npcs:
            if npc.can_interact(self.hitbox):
                self.nearby_npc = npc
                break

    def draw(self, screen):
        if self.zoom < 1:
            # Zoomed out: draw a bigger piece of the world, then shrink it to fit.
            view_size = (round(SCREEN_WIDTH / self.zoom), round(SCREEN_HEIGHT / self.zoom))
            if self.zoom_buffer is None:
                full = (round(SCREEN_WIDTH / PAN_ZOOM) + 2, round(SCREEN_HEIGHT / PAN_ZOOM) + 2)
                self.zoom_buffer = pygame.Surface(full).convert()
            view = self.zoom_buffer.subsurface((0, 0, *view_size))
            self.draw_world(view)
            screen.blit(pygame.transform.smoothscale(view, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))
        else:
            self.draw_world(screen)
        self.draw_hud(screen)

    # Draw the map and everything standing on it, shifted by the camera.
    def draw_world(self, screen):
        screen.fill((60, 90, 120))
        screen.blit(self.below, (-self.cam_x, -self.cam_y))
        for gate in self.gates:
            gate.draw(screen, self.cam_x, self.cam_y)

        # Sort by feet y: lower on screen is drawn later (in front).
        # The player is stored as None because it has no draw() method.
        drawables = [(npc.rect.bottom, npc) for npc in self.npcs]
        drawables += [(enemy.rect.bottom, enemy) for enemy in self.encounter.enemies]
        if self.wreck:
            drawables.append((self.wreck.sort_y, self.wreck))
        if self.gun_on_ground():
            drawables.append((self.gun.sort_y, self.gun))
        drawables.append((self.player_y + self.player_height, None))
        drawables.sort(key=lambda d: d[0])
        for _, obj in drawables:
            if obj is None:
                screen.blit(self.sprite.get_image(),
                            (self.player_x - self.cam_x, self.player_y - self.cam_y))
            else:
                obj.draw(screen, self.cam_x, self.cam_y)

        screen.blit(self.above, (-self.cam_x, -self.cam_y))
        if self.wreck:
            self.wreck.draw_smoke(screen, self.cam_x, self.cam_y)

    # Hint, HUD and popups, drawn on top of the world at normal size.
    def draw_hud(self, screen):
        # "Click / E" hint floating 8 px above the nearby NPC.
        if self.nearby_npc and not self.dialogue.active and not self.shop.is_open:
            hint_x = self.nearby_npc.rect.centerx - self.cam_x - self.talk_hint.get_width() // 2
            hint_y = self.nearby_npc.rect.top - self.cam_y - self.talk_hint.get_height() - 8
            screen.blit(self.talk_hint, (hint_x, hint_y))

        self.dialogue.draw(screen)
        # Minimap icons for shops and bosses still alive.
        markers = dict(shops=[npc.rect.center for npc in self.npcs if npc.shop_id],
                       npcs=[(npc.rect.center, npc.name) for npc in self.npcs if npc.on_minimap],
                       bosses=[self.boss.rect.center] if self.boss in self.encounter.enemies
                       and not self.boss.defeated else [])
        # During a dialogue (and its camera pans) and the whole crash intro,
        # only the text box is shown.
        if not self.dialogue.active and self.intro is None and self.repair is None:
            if not self.menu.is_open and not self.shop.is_open:
                self.menu_hint.draw(screen)
                self.objective.draw(screen, self.game.state.quest)
            state = self.game.state
            self.health_bar.draw(screen, state.hp, state.max_hp, self.last_dt)
            self.coin_counter.draw(screen, state.coins)
            self.fuel_counter.draw(screen, state.fuel, FUEL_NEEDED)
            self.minimap.draw(screen, self.hitbox.center, **markers)
        self.settings_panel.draw(screen)
        self.menu.draw(screen)
        self.shop.draw(screen)
        self.minimap.draw_expanded(screen, self.hitbox.center, **markers)

        # Crash fade: white overlay gets more transparent over time.
        if self.crash_fade > 0:
            self.white.set_alpha(round(255 * self.crash_fade / CRASH_FADE_TIME))
            screen.blit(self.white, (0, 0))
        # Jenny's reveal: full white, fading out.
        if self.flash > 0:
            self.white.set_alpha(round(255 * min(1.0, self.flash / FLASH_TIME * 1.5)))
            screen.blit(self.white, (0, 0))
        # Ship repair: white flash, then fade to black before the ending.
        white, black = self.repair_overlay()
        if white > 0:
            self.white.set_alpha(white)
            screen.blit(self.white, (0, 0))
        if black > 0:
            self.black.set_alpha(black)
            screen.blit(self.black, (0, 0))
