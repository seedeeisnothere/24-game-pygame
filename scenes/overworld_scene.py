import pygame
from settings import *
from systems.tilemap import *
from entities.player import *
from entities.enemy import Enemy, EnemyEncounter, EnemySpawner
from systems.settings_panel import SettingsPanel
from scenes.scene import Scene
from scenes.battle_scene import BattleScene
from entities.npc import NPC
from systems.dialouge import DialogueSystem
from systems.status_menu import StatusMenu
from entities.gate import Gate
from systems.hud import MenuHint, CoinCounter, HealthBar
from systems.minimap import Minimap
from systems.shop import ShopMenu
from entities.wreck import Wreck

WRECK_POS = (400, 2868)          # crashed ship, bottom-left of map 1
BOSS_POS = (2528, 1330)          # map 1 boss, guards the stone bridge
SHOP_NPC_POS = (3930, 1120)      # shopkeeper, next to the pond on the right
SHOP_NPC_SPRITE = "assets/sprites/npc/shopkeeper.png"
# Coin-farming area: the top-left dirt field (tiles 5-20 x 5-15).
FARM_ZONE = pygame.Rect(320, 300, 1024, 724)
FARM_WAVE_SIZE = (1, 2)          # min/max enemies per farm wave
FARM_RESPAWN_DISTANCE = 900      # walk this far away to respawn the farm
CRASH_FADE_TIME = 1.6            # seconds of white fade after the crash
TALK_LEAVE_REACH = 110           # walk farther than this to close talk/shop
TILE_PX = TILE * SCALE           # size of one tile on screen (64 px)


# World rectangle covering tiles, counted from the top-left tile (0, 0).
def tile_rect(col, row, cols=1, rows=1):
    return pygame.Rect(col * TILE_PX, row * TILE_PX, cols * TILE_PX, rows * TILE_PX)


# Center point of a tile; col 39.5 means halfway between two tiles.
def tile_point(col, row):
    return (round((col + 0.5) * TILE_PX), round((row + 0.5) * TILE_PX))


# Settings for each map:
#   spawn   = player's feet position on first visit (None = next to wreck)
#   boss    = boss top-left; beating it opens that map's gates
#   portals = list of (world area, target map, spawn there or None)
MAPS = {
    "map1": {
        "path": "data/maps/map1.json",
        "spawn": None,
        "boss": BOSS_POS,
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
        # Cave exit at the bottom leads back to the cave mouth on map 1.
        "portals": [(tile_rect(38, 45, 4, 2), "map1", tile_point(36.5, 7))],
        "minimap": {"water_layers": ["น้ำ"], "outline_solid": True},
    },
}


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

        # Enemies currently reuse the player's sprites.
        def make_enemy(x, y):
            return Enemy(x, y, "assets/sprites/player/idle.png", walk_paths,
                         walk_dir="assets/sprites/player/walk")

        self.boss = None
        self.farm = None
        self.encounter = EnemyEncounter([])
        if config.get("boss"):
            self.boss = make_enemy(*config["boss"])
            self.encounter.enemies.append(self.boss)
        # Only map 1 has the coin farm.
        if map_id == "map1":
            self.farm = EnemySpawner(FARM_ZONE, make_enemy, self.solid,
                                     wave_size=FARM_WAVE_SIZE,
                                     respawn_distance=FARM_RESPAWN_DISTANCE)
        self.menu_hint = MenuHint()
        self.coin_counter = CoinCounter()
        self.health_bar = HealthBar()
        self.minimap = Minimap(map_path, (self.world_width, self.world_height),
                               **config["minimap"])
        self.last_dt = 0.0

        self.gates = [Gate(tiles, rects) for tiles, rects in gate_data]

        self.dialogue = DialogueSystem("data/dialouge.json", (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.npcs = []
        if map_id == "map1":
            self.npcs.append(NPC("Elder", *SHOP_NPC_POS, SHOP_NPC_SPRITE, "npc_elder_01",
                                 shop_id="elder"))
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

    # Center the camera on the player, clamped to the map edges.
    def update_camera(self):
        self.cam_x = self.player_x + self.player_width // 2 - SCREEN_WIDTH // 2
        self.cam_y = self.player_y + self.player_height // 2 - SCREEN_HEIGHT // 2
        self.cam_x = max(0, min(self.cam_x, self.world_width - SCREEN_WIDTH))
        self.cam_y = max(0, min(self.cam_y, self.world_height - SCREEN_HEIGHT))

    def handle_events(self, events):
        # No input during the crash fade; dialogue takes all input when open.
        if self.crash_fade > 0:
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
                        self.start_battle(enemy)

    # Return the NPC under the mouse, but only if it is close enough to talk.
    def clicked_npc(self, mouse_pos):
        for npc in self.npcs:
            if npc.is_clicked(mouse_pos, self.cam_x, self.cam_y) and npc.can_interact(self.hitbox):
                return npc
        return None

    # Start dialogue; shop NPCs open their shop when the dialogue ends.
    def talk_to(self, npc):
        self.talking_npc = npc
        on_finish = (lambda: self.shop.open(npc.shop_id)) if npc.shop_id else None
        self.dialogue.start(npc, on_finish)

    def movement_locked(self):
        return self.dialogue.active or self.shop.is_open or self.menu.is_open

    def close_popups(self):
        self.dialogue.cancel()
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

    def update_farm(self):
        if self.farm is None:
            return
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

        keys = pygame.key.get_pressed()
        left = keys[pygame.K_LEFT] or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        up = keys[pygame.K_UP] or keys[pygame.K_w]
        down = keys[pygame.K_DOWN] or keys[pygame.K_s]
        if self.movement_locked() or self.leaving:
            left = right = up = down = False

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
        self.game.update_walk_sfx(self.sprite.moving)
        self.sprite.update(dt)

        # An enemy that catches the player starts a battle.
        self.update_farm()
        enemy = self.encounter.update(dt, self.hitbox, self.solid)
        if enemy:
            self.start_battle(enemy)

        self.update_camera()
        self.leave_npc_if_far()
        self.check_portals()

        self.nearby_npc = None
        for npc in self.npcs:
            if npc.can_interact(self.hitbox):
                self.nearby_npc = npc
                break

    def draw(self, screen):
        # World is drawn shifted by the camera offset.
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

        # "Click / E" hint floating 8 px above the nearby NPC.
        if self.nearby_npc and not self.dialogue.active and not self.shop.is_open:
            hint_x = self.nearby_npc.rect.centerx - self.cam_x - self.talk_hint.get_width() // 2
            hint_y = self.nearby_npc.rect.top - self.cam_y - self.talk_hint.get_height() - 8
            screen.blit(self.talk_hint, (hint_x, hint_y))

        # HUD and popups, drawn on top of the world.
        self.dialogue.draw(screen)
        if not self.menu.is_open and not self.shop.is_open:
            self.menu_hint.draw(screen)
        state = self.game.state
        self.health_bar.draw(screen, state.hp, state.max_hp, self.last_dt)
        self.coin_counter.draw(screen, state.coins)
        # Minimap icons for shops and bosses still alive.
        markers = dict(shops=[npc.rect.center for npc in self.npcs if npc.shop_id],
                       bosses=[self.boss.rect.center] if self.boss and not self.boss.defeated else [])
        self.minimap.draw(screen, self.hitbox.center, **markers)
        self.settings_panel.draw(screen)
        self.menu.draw(screen)
        self.shop.draw(screen)
        self.minimap.draw_expanded(screen, self.hitbox.center, **markers)

        # Crash fade: white overlay gets more transparent over time.
        if self.crash_fade > 0:
            self.white.set_alpha(round(255 * self.crash_fade / CRASH_FADE_TIME))
            screen.blit(self.white, (0, 0))
