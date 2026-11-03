import math
import random
import string
import pygame
from settings import *
from scenes.scene import Scene
from logic.game24 import Game24, OPS
from logic.puzzle_bank import load_puzzles, random_puzzle

PLAYER_MAX_HP = 5
ENEMY_MAX_HP = 5          # ถ้า Enemy มี .hp ของตัวเอง จะใช้ค่านั้นแทน
COMBO_TIME = 10.0         # เวลา (วินาที) ที่ต้องแก้ข้อถัดไปให้ทัน ไม่งั้น combo หาย
COMBO_MAX = 5
ATTACK_WAIT = (1.0, 3.0)  # ศัตรูเริ่มโจมตีรอบใหม่ทุก ๆ กี่วินาที (สุ่มในช่วงนี้)
WAVE_SIZES = (1, 1, 2, 3) # แต่ละรอบยิงกี่ลูก (สุ่มจากรายการนี้ ใส่เลขซ้ำ = มีโอกาสออกมากขึ้น, มากสุด 3)
ATTACK_GAP = (0.6, 1.1)   # ช่วงห่างระหว่างลูกในรอบเดียวกัน (วินาที)
DODGE_TIME = 1.8          # เวลานับถอยหลังให้กดหลบ "ต่อ 1 ลูก"
DODGE_KEYS = "ZWFXC"      # ตัวอักษรที่ใช้หลบ (ลูกที่ลอยอยู่พร้อมกันจะไม่ซ้ำตัวอักษร)
LANES_Y = (400, 470, 540) # ความสูงของแต่ละเลนที่ลูกโจมตีพุ่งผ่าน (= จำนวนลูกสูงสุดพร้อมกัน)
RESULT_TIME = 1.5         # ค้างหน้า WIN / DEFEATED ก่อนกลับ overworld
PANEL_X = 880             # เส้นแบ่งฝั่งซ้าย (ต่อสู้) / ฝั่งขวา (โจทย์ 24)

# ตัวอักษรบนปุ่มเครื่องหมาย (ฟอนต์อาจไม่มีตัว × ÷ จึงใช้ x กับ / ไปก่อน)
OP_LABELS = {"+": "+", "-": "-", "*": "x", "/": "/"}


LETTER_BY_SCANCODE = {getattr(pygame, f"KSCAN_{c}"): c for c in string.ascii_uppercase}

GOOD_COLOR = "#58B368"
BAD_COLOR = "#E0524A"


def format_value(value):
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


class BattleScene(Scene):
    """ฉากต่อสู้: แก้เกม 24 เพื่อโจมตี / กดตัวอักษรเพื่อหลบการโจมตีของศัตรู
    Esc = หนี (ไว้ทดสอบ)"""

    def __init__(self, game, enemy, overworld):
        super().__init__(game)
        self.enemy = enemy
        self.overworld = overworld

        self.big_font = pygame.font.Font(FONT_PATH, BUTTON_FONT_SIZE)
        self.small_font = pygame.font.Font(FONT_PATH, SMALL_FONT_SIZE)

        self.player_img = pygame.transform.scale(overworld.sprite.idle_right, (192, 261))
        self.enemy_img = pygame.transform.scale(enemy.sprite.idle_left, (192, 261))
        self.player_pos = (120, 330)
        self.enemy_pos = (590, 330)

        self.target_rect = pygame.Rect(920, 90, 320, 110)
        self.number_rects = [pygame.Rect(920 + col * 170, 250 + row * 140, 150, 120)
                             for row in range(2) for col in range(2)]
        self.op_rects = [pygame.Rect(920 + i * 82, 560, 72, 72) for i in range(4)]

        self.puzzles = load_puzzles()
        self.numbers = random_puzzle(self.puzzles)
        self.puzzle = Game24(self.numbers)

        self.player_hp = PLAYER_MAX_HP
        self.enemy_max_hp = getattr(enemy, "hp", ENEMY_MAX_HP)
        self.enemy_hp = self.enemy_max_hp

        self.combo = 0
        self.combo_timer = 0.0

        self.attacks = []
        self.wave_delays = []
        self.attack_timer = random.uniform(*ATTACK_WAIT)

        self.message = ""
        self.message_color = TEXT_COLOR
        self.message_timer = 0.0

        self.result = None
        self.result_timer = 0.0
        self.leaving = False

    # ---------- ควบคุม ----------
    def handle_events(self, events):
        for event in events:
            if self.result:
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.finish("flee")
                else:
                    self.press_letter(event.scancode)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.click(event.pos)
                elif event.button == 3:
                    self.puzzle.reset()

    def click(self, pos):
        for i, rect in enumerate(self.number_rects):
            if rect.collidepoint(pos):
                self.puzzle.click_number(i)
                self.check_puzzle()
                return
        for op, rect in zip(OPS, self.op_rects):
            if rect.collidepoint(pos):
                self.puzzle.click_op(op)
                return

    def check_puzzle(self):
        if self.puzzle.solved:
            self.hit_enemy()
        elif self.puzzle.failed:
            self.puzzle.reset()
            self.show("Not 24!", BAD_COLOR)

    def hit_enemy(self):
        self.combo = min(self.combo + 1, COMBO_MAX)
        self.combo_timer = COMBO_TIME
        damage = self.combo
        self.enemy_hp -= damage
        self.show(f"-{damage}", GOOD_COLOR)
        self.numbers = random_puzzle(self.puzzles, last=self.numbers)
        self.puzzle = Game24(self.numbers)
        if self.enemy_hp <= 0:
            self.finish("win")

    def press_letter(self, scancode):
        letter = LETTER_BY_SCANCODE.get(scancode)
        if letter is None or not self.attacks:
            return
        for attack in self.attacks:
            if attack["key"] == letter:
                self.attacks.remove(attack)
                self.show("Dodge!", GOOD_COLOR)
                return
        self.take_hit()

    def take_hit(self):
        self.player_hp -= 1
        self.show("Hit!", BAD_COLOR)
        if self.player_hp <= 0:
            self.finish("lose")

    def start_wave(self):
        delays, t = [], 0.0
        for _ in range(random.choice(WAVE_SIZES)):
            delays.append(t)
            t += random.uniform(*ATTACK_GAP)
        self.wave_delays = delays
        self.attack_timer = random.uniform(*ATTACK_WAIT)

    def spawn_attack(self):
        used_keys = {a["key"] for a in self.attacks}
        used_lanes = {a["lane"] for a in self.attacks}
        keys = [k for k in DODGE_KEYS if k not in used_keys]
        lanes = [i for i in range(len(LANES_Y)) if i not in used_lanes]
        if keys and lanes:
            self.attacks.append({"key": random.choice(keys), "left": DODGE_TIME,
                                 "lane": random.choice(lanes)})

    def show(self, text, color):
        self.message = text
        self.message_color = color
        self.message_timer = 0.8

    def finish(self, result):
        self.result = result
        self.attacks = []
        self.wave_delays = []
        if result == "win":
            self.enemy.defeated = True
            self.result_timer = RESULT_TIME
        elif result == "lose":
            self.enemy.stun(3.0)                    # TODO: ทำ game over จริงภายหลัง
            self.result_timer = RESULT_TIME
        else:
            self.enemy.stun(2.0)
            self.result_timer = 0.0

    def leave(self):
        if self.game.curtain.is_busy():
            return
        self.game.change_scene(lambda: self.overworld)
        self.leaving = True

    def update(self, dt):
        if self.result:
            self.result_timer -= dt
            if self.result_timer <= 0 and not self.leaving:
                self.leave()
            return

        if self.combo > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo = 0
                self.combo_timer = 0.0

        self.message_timer = max(0.0, self.message_timer - dt)

        if not self.attacks and not self.wave_delays:
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.start_wave()

        self.wave_delays = [d - dt for d in self.wave_delays]
        while self.wave_delays and self.wave_delays[0] <= 0:
            self.wave_delays.pop(0)
            self.spawn_attack()

        for attack in list(self.attacks):
            attack["left"] -= dt
            if attack["left"] <= 0:
                self.attacks.remove(attack)
                self.take_hit()
                if self.result:
                    break

    def text(self, screen, font, string_, color, **anchor):
        surface = font.render(string_, False, color)
        screen.blit(surface, surface.get_rect(**anchor))

    def draw_box(self, screen, rect, border_color, label=None, font=None):
        pygame.draw.rect(screen, BUTTON_FILL_COLOR, rect, border_radius=BUTTON_RADIUS)
        pygame.draw.rect(screen, border_color, rect, width=5, border_radius=BUTTON_RADIUS)
        if label is not None:
            self.text(screen, font or self.big_font, label, TEXT_COLOR, center=rect.center)

    def draw_hp_bar(self, screen, x, y, hp, max_hp):
        bar = pygame.Rect(x, y, 192, 16)
        pygame.draw.rect(screen, SLIDER_TRACK_COLOR, bar)
        fill = bar.copy()
        fill.width = int(bar.width * max(0, hp) / max_hp)
        pygame.draw.rect(screen, GOOD_COLOR, fill)
        pygame.draw.rect(screen, TEXT_COLOR, bar, 2)

    def draw(self, screen):
        screen.fill(TITLE_BG_COLOR)
        pygame.draw.line(screen, SLIDER_TRACK_COLOR, (PANEL_X, 30), (PANEL_X, SCREEN_HEIGHT - 30), 3)

        label = f"Combo x{self.combo}" if self.combo else "Combo"
        self.text(screen, self.small_font, label, TEXT_COLOR, topleft=(40, 28))
        bar = pygame.Rect(40, 76, 780, 30)
        pygame.draw.rect(screen, SLIDER_TRACK_COLOR, bar)
        fill = bar.copy()
        fill.width = int(bar.width * self.combo_timer / COMBO_TIME)
        pygame.draw.rect(screen, SLIDER_FILL_COLOR, fill)
        pygame.draw.rect(screen, BUTTON_COLOR, bar, 3)

        # ผู้เล่น / ศัตรู
        screen.blit(self.player_img, self.player_pos)
        screen.blit(self.enemy_img, self.enemy_pos)
        self.draw_hp_bar(screen, self.player_pos[0], self.player_pos[1] - 30, self.player_hp, PLAYER_MAX_HP)
        self.draw_hp_bar(screen, self.enemy_pos[0], self.enemy_pos[1] - 30, self.enemy_hp, self.enemy_max_hp)
        self.text(screen, self.small_font, "Player", TEXT_COLOR, midtop=(self.player_pos[0] + 96, 610))
        self.text(screen, self.small_font, self.enemy.name, TEXT_COLOR, midtop=(self.enemy_pos[0] + 96, 610))

        for attack in self.attacks:
            lane = attack["lane"]
            progress = 1 - attack["left"] / DODGE_TIME
            start_x = self.enemy_pos[0]
            end_x = self.player_pos[0] + 192
            x = start_x + (end_x - start_x) * progress
            pygame.draw.circle(screen, BAD_COLOR, (int(x), LANES_Y[lane]), 16)

            center = (self.player_pos[0] + 96 + (lane - 1) * 110, 250)
            pygame.draw.circle(screen, BUTTON_FILL_COLOR, center, 40)
            ring = pygame.Rect(0, 0, 90, 90)
            ring.center = center
            fraction = max(0.0, attack["left"] / DODGE_TIME)
            pygame.draw.arc(screen, BAD_COLOR, ring, math.pi / 2, math.pi / 2 + 2 * math.pi * fraction, 8)
            self.text(screen, self.big_font, attack["key"], TEXT_COLOR, center=center)

        if self.message_timer > 0:
            self.text(screen, self.big_font, self.message, self.message_color, center=(440, 200))

        mouse = pygame.mouse.get_pos()
        self.draw_box(screen, self.target_rect, BUTTON_COLOR, "24")
        for i, rect in enumerate(self.number_rects):
            value = self.puzzle.values[i]
            if value is None:
                continue
            selected = i == self.puzzle.first
            hovered = rect.collidepoint(mouse)
            color = BUTTON_HOVER_COLOR if selected or hovered else BUTTON_COLOR
            self.draw_box(screen, rect, color, format_value(value))
            if selected:
                pygame.draw.rect(screen, TEXT_COLOR, rect, width=2, border_radius=BUTTON_RADIUS)
        for op, rect in zip(OPS, self.op_rects):
            active = op == self.puzzle.op
            hovered = rect.collidepoint(mouse)
            color = BUTTON_HOVER_COLOR if active or hovered else BUTTON_COLOR
            self.draw_box(screen, rect, color, OP_LABELS[op])
        self.text(screen, self.small_font, "Right-click = reset", TEXT_COLOR, midtop=(1080, 670))

        if self.result in ("win", "lose"):
            overlay_text = "VICTORY" if self.result == "win" else "DEFEATED"
            self.text(screen, self.big_font, overlay_text, TEXT_COLOR, center=(440, 400))