import math
import string
import pygame
from settings import *
from scenes.scene import Scene
from logic.game24 import Game24, OPS
from logic.puzzle_bank import load_puzzles, random_puzzle
<<<<<<< Updated upstream
from logic.dodge import DodgeEvent
=======
from systems.game_state import HEAL_AMOUNT
from systems.icons import load_icon, dimmed
from systems.hud import CoinCounter
>>>>>>> Stashed changes

PLAYER_MAX_HP = 5
ENEMY_MAX_HP = 5          # ถ้า Enemy มี .hp ของตัวเอง จะใช้ค่านั้นแทน
COMBO_TIME = 15.0         # เวลา (วินาที) ที่ต้องแก้ข้อถัดไปให้ทัน ไม่งั้น combo หาย
COMBO_MAX = 5
COMBO_WARNING_TIME = 3.0
COMBO_BLINK_TIME = 0.25
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

        self.dodge = DodgeEvent(len(LANES_Y))

        self.message = ""
        self.message_color = TEXT_COLOR
        self.message_timer = 0.0

        self.result = None
        self.result_timer = 0.0
        self.leaving = False
<<<<<<< Updated upstream
=======
        self.player_max_hp = game.state.max_hp
        self.player_hp = game.state.hp
        self.heal_icon = load_icon(POTION_ICON_PATH, 48)
        self.heal_icon_dim = dimmed(self.heal_icon)
        self.coins_earned = 0
        self.coin_counter = CoinCounter()


>>>>>>> Stashed changes

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
        self.dodge.press(LETTER_BY_SCANCODE.get(scancode))
        self.apply_dodge_results()

    def apply_dodge_results(self):
        for result in self.dodge.consume_results():
            if self.result:
                break
            if result == "dodged":
                self.show("Dodge!", GOOD_COLOR)
            else:
                self.take_hit()

    def take_hit(self):
        self.player_hp -= 1
        self.show("Hit!", BAD_COLOR)
        if self.player_hp <= 0:
            self.finish("lose")

    def show(self, text, color):
        self.message = text
        self.message_color = color
        self.message_timer = 0.8

    def finish(self, result):
        self.result = result
        self.dodge.clear()
        if result == "win":
            self.enemy.defeated = True
            self.coins_earned = random.randint(*self.enemy.coin_reward)
            self.game.state.add_coins(self.coins_earned)
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

        self.dodge.update(dt)
        self.apply_dodge_results()

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
        fill_color = SLIDER_FILL_COLOR
        if self.combo > 0 and self.combo_timer <= COMBO_WARNING_TIME:
            if int(self.combo_timer / COMBO_BLINK_TIME) % 2 == 0:
                fill_color = BAD_COLOR
        pygame.draw.rect(screen, fill_color, fill)
        pygame.draw.rect(screen, BUTTON_COLOR, bar, 3)

        # ผู้เล่น / ศัตรู
        screen.blit(self.player_img, self.player_pos)
        screen.blit(self.enemy_img, self.enemy_pos)
        self.draw_hp_bar(screen, self.player_pos[0], self.player_pos[1] - 30, self.player_hp, PLAYER_MAX_HP)
        self.draw_hp_bar(screen, self.enemy_pos[0], self.enemy_pos[1] - 30, self.enemy_hp, self.enemy_max_hp)
        self.text(screen, self.small_font, "Player", TEXT_COLOR, midtop=(self.player_pos[0] + 96, 610))
        self.text(screen, self.small_font, self.enemy.name, TEXT_COLOR, midtop=(self.enemy_pos[0] + 96, 610))

<<<<<<< Updated upstream
        for attack in self.dodge.attacks:
=======
        if self.result == "win":
            self.text(screen, self.small_font, f"+{self.coins_earned} coins", TEXT_COLOR, center=(440, 460))

        for attack in self.attacks:
>>>>>>> Stashed changes
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