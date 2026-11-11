import pygame
from settings import *
from systems.tilemap import *
from entities.player import *
from entities.enemy import Enemy, EnemyEncounter
from systems.settings_panel import SettingsPanel
from scenes.scene import Scene
from scenes.battle_scene import BattleScene
from entities.npc import NPC
from systems.dialouge import DialogueSystem
from systems.status_menu import StatusMenu
from systems.hud import MenuHint, CoinCounter


class OverworldScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.below, self.above = load_map(MAP_PATH)
        self.solid = load_collision(MAP_PATH)
        self.world_width = self.below.get_width()
        self.world_height = self.below.get_height()

        walk_paths = [f"Walk{i}.png" for i in range(12)]
        self.sprite = AnimatedSprite("assets/sprites/player/idle.png", walk_paths, frame_duration_ms=WALK_FRAME_MS)
        player_rect = self.sprite.idle_right.get_rect(center=self.game.screen_rect.center)
        self.player_x = player_rect.x
        self.player_y = player_rect.y
        self.player_width = player_rect.width
        self.player_height = player_rect.height
        self.hitbox = pygame.Rect(0, 0, HITBOX_WIDTH, HITBOX_HEIGHT)
        self.hitbox_offset_x = (self.player_width - HITBOX_WIDTH) // 2
        self.hitbox_offset_y = self.player_height - HITBOX_HEIGHT
        self.cam_x = 0
        self.cam_y = 0
        self.settings_panel = SettingsPanel(game, in_game=True)

        # ศัตรูตัวอย่าง: ตอนนี้ยืมสไปรต์ผู้เล่นไปก่อน เปลี่ยน path เมื่อมีรูปศัตรูจริง
        # และควรวางตำแหน่งให้อยู่บนพื้นที่เดินได้ (ไม่ทับ collision)
        self.encounter = EnemyEncounter([
            Enemy(self.player_x + 300, self.player_y,
                  "assets/sprites/player/idle.png", walk_paths,
                  walk_dir="assets/sprites/player/walk"),
        ])
        self.menu_hint = MenuHint()
        self.coin_counter = CoinCounter()


        self.dialogue = DialogueSystem("data/dialouge.json", (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.npcs = [
            NPC("ผู้เฒ่า", 600, 500, "assets/sprites/npc/elder.png", "npc_elder_01"),
        ]
        self.nearby_npc = None

    def handle_events(self, events):
        if self.dialogue.active:
            self.dialogue.handle_events(events)
            return

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.settings_panel.is_active():
                    self.settings_panel.close()
                else:
                    self.settings_panel.open()
            elif self.settings_panel.is_active():
                self.settings_panel.handle_event(event)
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_e):
                enemy = self.encounter.enemy_in_front(self.hitbox, self.sprite.facing_right)
                if enemy:
                    self.start_battle(enemy)

    def start_battle(self, enemy):
        self.game.change_scene(lambda: BattleScene(self.game, enemy, self))

    def update(self, dt):
        if self.dialogue.active:
            self.sprite.moving = False
            self.sprite.update(dt)
            return
        
        self.settings_panel.update(dt, pygame.mouse.get_pos())
        if self.settings_panel.is_active():
            return
        keys = pygame.key.get_pressed()
        left  = keys[pygame.K_LEFT]  or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        up    = keys[pygame.K_UP]    or keys[pygame.K_w]
        down  = keys[pygame.K_DOWN]  or keys[pygame.K_s]

        if right and not left:
            self.sprite.facing_right = True
        elif left and not right:
            self.sprite.facing_right = False

        dx = right - left
        dy = down - up
        step = WALK_SPEED
        if dx != 0 and dy != 0:
            step = WALK_SPEED * 3 // 4

        old_x = self.player_x
        old_y = self.player_y

        self.player_x += dx * step
        self.player_x = max(0, min(self.player_x, self.world_width - self.player_width))
        self.hitbox.topleft = (self.player_x + self.hitbox_offset_x, self.player_y + self.hitbox_offset_y)
        if touches_solid(self.hitbox, self.solid):
            self.player_x = old_x

        self.player_y += dy * step
        self.player_y = max(0, min(self.player_y, self.world_height - self.player_height))
        self.hitbox.topleft = (self.player_x + self.hitbox_offset_x, self.player_y + self.hitbox_offset_y)
        if touches_solid(self.hitbox, self.solid):
            self.player_y = old_y

        # รีเซ็ต hitbox ให้ตรงตำแหน่งสุดท้ายจริง (กรณีโดนถอยกลับจาก collision)
        self.hitbox.topleft = (self.player_x + self.hitbox_offset_x, self.player_y + self.hitbox_offset_y)

        self.sprite.moving = self.player_x != old_x or self.player_y != old_y
        self.game.update_walk_sfx(self.sprite.moving)
        self.sprite.update(dt)

        enemy = self.encounter.update(dt, self.hitbox, self.solid)
        if enemy:
            self.start_battle(enemy)

        self.cam_x = self.player_x + self.player_width // 2 - SCREEN_WIDTH // 2
        self.cam_y = self.player_y + self.player_height // 2 - SCREEN_HEIGHT // 2
        self.cam_x = max(0, min(self.cam_x, self.world_width - SCREEN_WIDTH))
        self.cam_y = max(0, min(self.cam_y, self.world_height - SCREEN_HEIGHT))

        self.nearby_npc = None
        for npc in self.npcs:
            if npc.can_interact(self.hitbox):
                self.nearby_npc = npc
                break

    def draw(self, screen):
        screen.fill((60, 90, 120))
        screen.blit(self.below, (-self.cam_x, -self.cam_y))

        # เรียงตามเท้า: ใครอยู่ต่ำกว่าบนจอ วาดทีหลัง
        drawables = [(npc.rect.bottom, npc) for npc in self.npcs]
        drawables.append((self.player_y + self.player_height, None))
        drawables.sort(key=lambda d: d[0])
        for _, obj in drawables:
            if obj is None:
                screen.blit(self.sprite.get_image(),
                            (self.player_x - self.cam_x, self.player_y - self.cam_y))
            else:
                obj.draw(screen, self.cam_x, self.cam_y)

        screen.blit(self.above, (-self.cam_x, -self.cam_y))

        # ป้าย "กด E"
        if self.nearby_npc and not self.dialogue.active:
            # วาดเหนือหัว NPC (ใช้ฟอนต์ที่รองรับไทยเหมือนกัน)
            pass  # เติมทีหลังได้

        self.dialogue.draw(screen)
        if not self.menu.is_open:
            self.menu_hint.draw(screen)
        self.coin_counter.draw(screen, self.game.state.coins)
        self.settings_panel.draw(screen)
        self.menu.draw(screen)
