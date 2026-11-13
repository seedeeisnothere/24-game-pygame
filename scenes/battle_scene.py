import math
import random
import string
import pygame
from systems.dialogue import PLAYER_NAME
from settings import *
from scenes.scene import Scene
from logic.game24 import Game24, OPS
from logic.puzzle_bank import load_puzzles, random_puzzle
from systems.game_state import HEAL_AMOUNT
from systems.icons import load_icon, dimmed
from systems.hud import CoinCounter
from systems.gun_shot import GunShot
from systems.battle_fx import Tackle, Beam, PlayerMotion, draw_orb

COMBO_TIME = 10.0                  # seconds before the combo resets
COMBO_MAX = 5                      # highest combo (= highest damage per solve)
LANES_Y = (400, 470, 540)          # y position of each attack lane
RESULT_TIME = 1.5                  # seconds to show VICTORY/DEFEATED
PANEL_X = 880                      # x of the line between fight and puzzle
HEAL_RECT = pygame.Rect(40, 700, 90, 90)
SKIP_RECT = pygame.Rect(190, 700, 90, 90)

OP_LABELS = {"+": "+", "-": "-", "*": "x", "/": "/"}

# Maps keyboard scancodes to letters, so dodging works on any layout.
LETTER_BY_SCANCODE = {getattr(pygame, f"KSCAN_{c}"): c for c in string.ascii_uppercase}

GOOD_COLOR = "#58B368"
BAD_COLOR = "#E0524A"
FAILED_COLOR = "#5A6480"


# Turn a Fraction into text: "3" or "7/2".
def format_value(value):
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


# Bosses float slowly up and down in battle (not the final boss), like the
# title planet (10 px, 4 s) but a little faster.
BOSS_FLOAT_HEIGHT = 10      # pixels up and down from the resting spot
BOSS_FLOAT_TIME = 3.0       # seconds for one full up-and-down

# Each boss fires its beam in its own color.
BEAM_COLORS = {
    "boss_forest": "#E0524A",
    "boss_cave": "#4AA8FF",
    "boss_final": "#B65CFF",
}
TACKLE_OVERLAP = 40         # how far the slime squishes into the player

# Battle: solve 24 puzzles to hit the enemy, type letters to dodge attacks.
class BattleScene(Scene):
    def __init__(self, game, enemy, overworld):
        super().__init__(game)
        self.enemy = enemy
        self.overworld = overworld
        is_boss = (enemy.kind or "").startswith("boss")
        self.music = "boss" if is_boss else "battle"

        self.big_font = pygame.font.Font(FONT_PATH, BUTTON_FONT_SIZE)
        self.small_font = pygame.font.Font(FONT_PATH, SMALL_FONT_SIZE)

        # Big copies of the overworld sprites, facing each other.
        self.player_img = pygame.transform.scale(overworld.sprite.idle_right, (192, 261))
        # Slimes bring their own crisp big image; others get stretched like the player.
        self.enemy_img = getattr(enemy.sprite, "battle_image", None)
        if self.enemy_img is None:
            self.enemy_img = pygame.transform.scale(enemy.sprite.idle_left, (192, 261))
        self.player_pos = (120, 330)
        # Stand on the same floor line as the player, centered in a 192px slot.
        self.enemy_pos = (590 + (192 - self.enemy_img.get_width()) // 2,
                          330 + 261 - self.enemy_img.get_height())
        # Floating bosses: every boss except the final one (Jenny).
        kind = enemy.kind or ""
        self.boss_floats = kind.startswith("boss") and kind != "boss_final"
        self.boss_timer = 0.0

        # Enemy attack animations: bosses fire beams, everything else tackles.
        # strikes: attacks that have launched, as {"fx": Tackle/Beam, "dodged": bool}.
        self.attack_style = "beam" if is_boss else "tackle"
        self.beam_color = BEAM_COLORS.get(kind, BAD_COLOR)
        self.strikes = []
        # Player dodge hop, after-images and red hurt flash.
        self.player_motion = PlayerMotion()
        self.player_ghost_img = self.player_img.copy()
        self.player_ghost_img.set_alpha(70)
        self.player_hurt_img = self.player_img.copy()
        self.player_hurt_img.fill((255, 70, 70), special_flags=pygame.BLEND_RGB_MULT)

        # Puzzle panel layout: target box, 2x2 number cards, 4 operator buttons.
        self.target_rect = pygame.Rect(920, 90, 320, 110)
        self.number_rects = [pygame.Rect(920 + col * 170, 250 + row * 140, 150, 120)
                             for row in range(2) for col in range(2)]
        self.op_rects = [pygame.Rect(920 + i * 82, 560, 72, 72) for i in range(4)]

        self.puzzles = load_puzzles()
        self.numbers = random_puzzle(self.puzzles)
        self.puzzle = Game24(self.numbers)

        self.player_max_hp = game.state.max_hp
        self.player_hp = self.player_max_hp

        # Enemy attack settings come from the enemy's data.
        battle = enemy.battle
        self.attack_wait = tuple(battle["attack_wait"])
        self.wave_sizes = battle["wave_sizes"]
        self.attack_gap = tuple(battle["attack_gap"])
        self.dodge_time = battle["dodge_time"]
        self.dodge_keys = battle["dodge_keys"]
        # Each attack in a wave needs its own lane and its own letter.
        if max(self.wave_sizes) > len(LANES_Y) or len(self.dodge_keys) < max(self.wave_sizes):
            raise ValueError(
                f"{enemy.name}: wave_sizes must be <= {len(LANES_Y)} "
                f"and dodge_keys must have at least as many letters")
        self.enemy_max_hp = enemy.hp
        self.enemy_hp = self.enemy_max_hp

        self.combo = 0
        self.combo_timer = 0.0

        # attacks: incoming attacks; wave_delays: when the next ones spawn.
        self.attacks = []
        self.wave_delays = []
        self.attack_timer = random.uniform(*self.attack_wait)

        self.message = ""
        self.message_color = TEXT_COLOR
        self.message_timer = 0.0

        # result is None while fighting, then "win", "lose" or "flee".
        self.result = None
        self.result_timer = 0.0
        self.leaving = False
        # Overrides the values above: start with the player's current HP.
        self.player_max_hp = game.state.max_hp
        self.player_hp = game.state.hp
        self.heal_icon = load_icon(POTION_ICON_PATH, 48)
        self.heal_icon_dim = dimmed(self.heal_icon)
        self.skip_icon = load_icon(SKIP_ICON_PATH, 40)
        self.skip_icon_dim = dimmed(self.skip_icon)
        self.coins_earned = 0
        self.coin_counter = CoinCounter()

        # Quickdraw: the gun comes out of the player's hip and shoots the enemy.
        # The enemy HP bar only drops when the bullet lands (shown_enemy_hp).
        enemy_rect = self.enemy_img.get_rect(topleft=self.enemy_pos)
        self.gun = GunShot(hip=(self.player_pos[0] + 150, self.player_pos[1] + 182),
                           aim=(self.player_pos[0] + 200, self.player_pos[1] + 130),
                           enemy_rect=enemy_rect)
        self.shown_enemy_hp = self.enemy_hp
        self.enemy_flash_img = self.enemy_img.copy()
        self.enemy_flash_img.fill((255, 255, 255, 0), special_flags=pygame.BLEND_RGBA_MAX)

    def handle_events(self, events):
        for event in events:
            # Ignore input once the battle has ended.
            if self.result:
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.finish("flee")
                elif event.scancode == pygame.KSCAN_Q:
                    self.use_potion()
                elif event.scancode == pygame.KSCAN_E:
                    self.use_skip()
                else:
                    self.press_letter(event.scancode)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.click(event.pos)
                elif event.button == 3:
                    self.puzzle.reset()

    # Left click on a number card or an operator button.
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

    # After a move: hit the enemy if solved, reset if the answer is wrong.
    def check_puzzle(self):
        if self.puzzle.solved:
            self.hit_enemy()
        elif self.puzzle.failed:
            self.puzzle.reset()
            self.show("Not 24!", BAD_COLOR)

    # Damage = combo + shop bonus, then load a new puzzle.
    def hit_enemy(self):
        self.combo = min(self.combo + 1, COMBO_MAX)
        self.combo_timer = COMBO_TIME
        damage = self.combo + self.game.state.damage_bonus
        # A new shot before the last bullet landed: catch the HP bar up first.
        self.shown_enemy_hp = self.enemy_hp
        self.enemy_hp -= damage
        self.gun.start()
        self.show(f"-{damage}", GOOD_COLOR)
        self.numbers = random_puzzle(self.puzzles, last=self.numbers)
        self.puzzle = Game24(self.numbers)
        if self.enemy_hp <= 0:
            self.finish("win")

    # Dodge the attack with this letter; a wrong letter fails the closest one.
    def press_letter(self, scancode):
        letter = LETTER_BY_SCANCODE.get(scancode)
        live = [a for a in self.attacks if not a["failed"]]
        if letter is None or not live:
            return
        for attack in live:
            if attack["key"] == letter:
                # Dodged: the enemy attacks right away and the player hops clear.
                self.attacks.remove(attack)
                self.launch(attack, dodged=True)
                self.show("Dodge!", GOOD_COLOR)
                return
        # Pressing the letter of an already-failed attack does nothing.
        if any(a["key"] == letter for a in self.attacks):
            return
        # Wrong letter: the attack closest to landing can't be dodged now.
        min(live, key=lambda a: a["left"])["failed"] = True
        self.show("Miss!", BAD_COLOR)

    # Start the enemy's attack animation for this attack. Dodged attacks
    # miss (the player hops over them); the rest hit when they land.
    def launch(self, attack, dodged):
        if self.attack_style == "beam":
            fx = Beam(LANES_Y[attack["lane"]], self.beam_color)
        else:
            reach = self.player_pos[0] + self.player_img.get_width() - TACKLE_OVERLAP
            fx = Tackle(self.enemy_pos[0] - reach)
        self.strikes.append({"fx": fx, "dodged": dodged})
        if dodged:
            self.player_motion.dodge()

    # Advance the attack animations; undodged ones hurt when they land.
    def update_strikes(self, dt):
        for strike in list(self.strikes):
            if strike["fx"].update(dt) == "impact" and not strike["dodged"] and not self.result:
                self.take_hit()
            if strike["fx"].done:
                self.strikes.remove(strike)

    # The tackle that is moving the enemy right now (the newest one), if any.
    def current_tackle(self):
        for strike in reversed(self.strikes):
            if isinstance(strike["fx"], Tackle):
                return strike["fx"]
        return None

    # An attack reached the player.
    def take_hit(self):
        self.player_motion.hurt()
        self.player_hp -= 1
        self.show("Hit!", BAD_COLOR)
        if self.player_hp <= 0:
            self.game.play_sfx("death")
            self.finish("lose")

    # Drink a potion (Q key) if we have one and are not at full HP.
    def use_potion(self):
        state = self.game.state
        if state.potions <= 0:
            self.show("No potion", BAD_COLOR)
            return
        if self.player_hp >= self.player_max_hp:
            self.show("HP full", BAD_COLOR)
            return
        state.potions -= 1
        healed = min(HEAL_AMOUNT, self.player_max_hp - self.player_hp)
        self.player_hp += healed
        self.show(f"+{healed}", GOOD_COLOR)

    # Use a skip ticket (E key): swap the puzzle for a new one, no damage dealt.
    def use_skip(self):
        state = self.game.state
        if state.skips <= 0:
            self.show("No skip", BAD_COLOR)
            return
        state.skips -= 1
        self.numbers = random_puzzle(self.puzzles, last=self.numbers)
        self.puzzle = Game24(self.numbers)
        self.show("Skipped!", GOOD_COLOR)

    # Plan a wave: a list of delays, one per attack, spaced randomly.
    def start_wave(self):
        delays, t = [], 0.0
        for _ in range(random.choice(self.wave_sizes)):
            delays.append(t)
            t += random.uniform(*self.attack_gap)
        self.wave_delays = delays
        self.attack_timer = random.uniform(*self.attack_wait)

    # Add one attack using a letter and lane not already in use.
    def spawn_attack(self):
        used_keys = {a["key"] for a in self.attacks}
        used_lanes = {a["lane"] for a in self.attacks}
        keys = [k for k in self.dodge_keys if k not in used_keys]
        lanes = [i for i in range(len(LANES_Y)) if i not in used_lanes]
        if keys and lanes:
            # "left" = seconds until the attack hits the player.
            self.attacks.append({"key": random.choice(keys), "left": self.dodge_time,
                                 "lane": random.choice(lanes), "failed": False})

    # Show a short popup message for 0.8 seconds.
    def show(self, text, color):
        self.message = text
        self.message_color = color
        self.message_timer = 0.8

    # End the battle, save HP and give rewards or stun the enemy.
    def finish(self, result):
        self.result = result
        # The overworld reads this when we return (story lines after a boss, etc.)
        self.overworld.battle_result = (self.enemy, result)
        self.game.state.set_hp(self.player_hp)
        self.attacks = []
        self.wave_delays = []
        if result == "win":
            self.enemy.defeated = True
            self.game.state.record_kill(self.enemy.kind)
            self.coins_earned = random.randint(*self.enemy.coin_reward)
            self.game.state.add_coins(self.coins_earned)
            self.result_timer = RESULT_TIME
        elif result == "lose":
            self.enemy.stun(3.0)
            self.result_timer = RESULT_TIME
        else:
            # Fleeing: stun the enemy briefly so it doesn't re-catch you.
            self.enemy.stun(2.0)
            self.result_timer = 0.0

    # Go to game over if we lost, otherwise back to the same overworld.
    def leave(self):
        if self.game.curtain.is_busy():
            return
        if self.result == "lose":
            self.game.change_scene("gameover")
        else:
            self.game.change_scene(lambda: self.overworld)
        self.leaving = True

    def update(self, dt):
        # Boss float keeps going, even after the battle ends.
        self.boss_timer += dt

        # The gun animation also keeps going, so the winning shot still lands.
        gun_event = self.gun.update(dt)
        if gun_event == "fire":
            self.game.play_sfx("shoot")
        elif gun_event == "hit":
            self.game.play_sfx("hit")
            self.shown_enemy_hp = self.enemy_hp

        # Attack and dodge animations also finish playing after the battle ends.
        self.player_motion.update(dt)
        self.update_strikes(dt)

        # Battle over: wait for the result timer, then leave once.
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

        # Count down to the next wave only when the screen is clear.
        if not self.attacks and not self.wave_delays:
            self.attack_timer -= dt
            if self.attack_timer <= 0:
                self.start_wave()

        # Spawn each planned attack when its delay runs out.
        self.wave_delays = [d - dt for d in self.wave_delays]
        while self.wave_delays and self.wave_delays[0] <= 0:
            self.wave_delays.pop(0)
            self.spawn_attack()

        # Timer ran out (not dodged in time, or a wrong letter was pressed):
        # the enemy launches the attack and it will hit when it lands.
        # Iterate over a copy because we remove attacks inside the loop.
        for attack in list(self.attacks):
            attack["left"] -= dt
            if attack["left"] <= 0:
                self.attacks.remove(attack)
                self.launch(attack, dodged=False)

    # Helper: render text and place it using a rect anchor like center=(x, y).
    def text(self, screen, font, string_, color, **anchor):
        surface = font.render(string_, False, color)
        screen.blit(surface, surface.get_rect(**anchor))

    # Draw a rounded box with a border and an optional centered label.
    def draw_box(self, screen, rect, border_color, label=None, font=None):
        pygame.draw.rect(screen, BUTTON_FILL_COLOR, rect, border_radius=BUTTON_RADIUS)
        pygame.draw.rect(screen, border_color, rect, width=5, border_radius=BUTTON_RADIUS)
        if label is not None:
            self.text(screen, font or self.big_font, label, TEXT_COLOR, center=rect.center)

    # Draw an HP bar whose fill width is the HP fraction.
    def draw_hp_bar(self, screen, x, y, hp, max_hp):
        bar = pygame.Rect(x, y, 192, 16)
        pygame.draw.rect(screen, SLIDER_TRACK_COLOR, bar)
        fill = bar.copy()
        fill.width = int(bar.width * max(0, hp) / max_hp)
        pygame.draw.rect(screen, GOOD_COLOR, fill)
        pygame.draw.rect(screen, TEXT_COLOR, bar, 2)

    # Player: after-images while dodging, then the player, then a red hurt flash.
    def draw_player(self, screen):
        x, y = self.player_pos
        for dx, dy in self.player_motion.ghost_offsets():
            screen.blit(self.player_ghost_img, (x + dx, y + dy))
        dx, dy = self.player_motion.offset()
        screen.blit(self.player_img, (x + dx, y + dy))
        flash = self.player_motion.hurt_flash()
        if flash > 0:
            self.player_hurt_img.set_alpha(round(200 * flash))
            screen.blit(self.player_hurt_img, (x + dx, y + dy))

    # Enemy: tackle lunge + squash, beam recoil, a nervous wobble when a slime
    # is about to tackle, and the gun's hit shake/flash. Returns the left x.
    def draw_enemy(self, screen, bob):
        img, flash_img = self.enemy_img, self.enemy_flash_img
        x, y = self.enemy_pos[0], self.enemy_pos[1] + bob
        tackle = self.current_tackle()
        if tackle:
            dx, dy = tackle.offset()
            x, y = x + dx, y + dy
            sx, sy = tackle.squash()
            if (sx, sy) != (1.0, 1.0):
                # Squash around the bottom middle so the slime stays on the floor.
                w, h = img.get_size()
                size = (round(w * sx), round(h * sy))
                img = pygame.transform.scale(img, size)
                flash_img = pygame.transform.scale(flash_img, size)
                x += (w - size[0]) // 2
                y += h - size[1]
        for strike in self.strikes:
            if isinstance(strike["fx"], Beam):
                x += strike["fx"].recoil()
        if self.attack_style == "tackle" and not tackle and self.attacks and not self.result:
            # Gets twitchier as the attack timer runs out.
            urgency = 1 - min(a["left"] for a in self.attacks) / self.dodge_time
            if urgency > 0.5:
                x += math.sin(self.boss_timer * 50) * 6 * (urgency - 0.5) * 2
        shake_x, shake_y = self.gun.enemy_shake()
        at = (round(x + shake_x), round(y + shake_y))
        screen.blit(img, at)
        flash = self.gun.enemy_flash()
        if flash > 0:
            flash_img.set_alpha(round(220 * flash))
            screen.blit(flash_img, at)
        return round(x)

    def draw(self, screen):
        screen.fill(TITLE_BG_COLOR)
        pygame.draw.line(screen, SLIDER_TRACK_COLOR, (PANEL_X, 30), (PANEL_X, SCREEN_HEIGHT - 30), 3)

        # Combo bar shrinks as the combo timer runs out.
        label = f"Combo x{self.combo}" if self.combo else "Combo"
        self.text(screen, self.small_font, label, TEXT_COLOR, topleft=(40, 28))
        bar = pygame.Rect(40, 76, 780, 30)
        pygame.draw.rect(screen, SLIDER_TRACK_COLOR, bar)
        fill = bar.copy()
        fill.width = int(bar.width * self.combo_timer / COMBO_TIME)
        pygame.draw.rect(screen, SLIDER_FILL_COLOR, fill)
        pygame.draw.rect(screen, BUTTON_COLOR, bar, 3)

        # Fighters, HP bars and names (96 = half the sprite width).
        self.draw_player(screen)
        bob = 0
        if self.boss_floats:
            bob = round(math.sin(self.boss_timer / BOSS_FLOAT_TIME * math.tau) * BOSS_FLOAT_HEIGHT)
        enemy_x = self.draw_enemy(screen, bob)
        self.draw_hp_bar(screen, self.player_pos[0], self.player_pos[1] - 30,
                         self.player_hp, self.player_max_hp)
        self.draw_hp_bar(screen, 590, self.enemy_pos[1] - 30,
                         self.shown_enemy_hp, self.enemy_max_hp)
        self.text(screen, self.small_font, PLAYER_NAME, TEXT_COLOR,
                  midtop=(self.player_pos[0] + 96, 610))
        self.text(screen, self.small_font, self.enemy.name, TEXT_COLOR,
                  midtop=(590 + 96, 610))

        if self.result == "win":
            self.text(screen, self.small_font, f"+{self.coins_earned} coins", TEXT_COLOR,
                      center=(440, 460))

        # Beams fly in front of both fighters.
        beam_x = enemy_x + 20
        for strike in self.strikes:
            if isinstance(strike["fx"], Beam):
                strike["fx"].draw(screen, beam_x, bob)

        for attack in self.attacks:
            lane = attack["lane"]
            # Bosses charge an orb for each waiting attack; it grows until it fires.
            if self.attack_style == "beam":
                progress = 1 - attack["left"] / self.dodge_time
                pulse = 1 + 0.12 * math.sin(self.boss_timer * 18)
                draw_orb(screen, self.beam_color, (beam_x, LANES_Y[lane] + bob),
                         (5 + 9 * progress) * pulse)

            # Letter bubble above the player; lane 0/1/2 = left/middle/right.
            center = (self.player_pos[0] + 96 + (lane - 1) * 110, 250)
            pygame.draw.circle(screen, BUTTON_FILL_COLOR, center, 40)
            ring = pygame.Rect(0, 0, 90, 90)
            ring.center = center
            # Timer ring: an arc from the top that shrinks as time runs out.
            fraction = max(0.0, attack["left"] / self.dodge_time)
            ring_color = FAILED_COLOR if attack["failed"] else BAD_COLOR
            pygame.draw.arc(screen, ring_color, ring, math.pi / 2,
                            math.pi / 2 + 2 * math.pi * fraction, 8)
            if attack["failed"]:
                self.text(screen, self.big_font, "X", BAD_COLOR, center=center)
            else:
                self.text(screen, self.big_font, attack["key"], TEXT_COLOR, center=center)

        self.gun.draw(screen)

        if self.message_timer > 0:
            self.text(screen, self.big_font, self.message, self.message_color, center=(440, 200))

        # Puzzle panel: target, number cards (used ones are None) and operators.
        mouse = pygame.mouse.get_pos()
        self.draw_box(screen, self.target_rect, BUTTON_COLOR, "GAME 24")
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

        # Potion button: greyed out when we have none.
        potions = self.game.state.potions
        border = BUTTON_COLOR if potions > 0 else FAILED_COLOR
        self.draw_box(screen, HEAL_RECT, border)
        icon = self.heal_icon if potions > 0 else self.heal_icon_dim
        screen.blit(icon, icon.get_rect(center=(HEAL_RECT.centerx, HEAL_RECT.top + 32)))
        self.text(screen, self.small_font, f"x{potions}", TEXT_COLOR,
                  midbottom=(HEAL_RECT.centerx, HEAL_RECT.bottom - 4))
        self.text(screen, self.small_font, "Q", TEXT_COLOR,
                  midleft=(HEAL_RECT.right + 12, HEAL_RECT.centery))

        # Skip button: greyed out when we have no tickets.
        skips = self.game.state.skips
        self.draw_box(screen, SKIP_RECT, BUTTON_COLOR if skips > 0 else FAILED_COLOR)
        icon = self.skip_icon if skips > 0 else self.skip_icon_dim
        screen.blit(icon, icon.get_rect(center=(SKIP_RECT.centerx, SKIP_RECT.top + 32)))
        self.text(screen, self.small_font, f"x{skips}", TEXT_COLOR,
                  midbottom=(SKIP_RECT.centerx, SKIP_RECT.bottom - 4))
        self.text(screen, self.small_font, "E", TEXT_COLOR,
                  midleft=(SKIP_RECT.right + 12, SKIP_RECT.centery))

        if self.result in ("win", "lose"):
            overlay_text = "VICTORY" if self.result == "win" else "DEFEATED"
            self.text(screen, self.big_font, overlay_text, TEXT_COLOR, center=(440, 400))
