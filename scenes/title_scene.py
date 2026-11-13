import math
import pygame
from settings import *
from scenes.scene import Scene
from systems.ui import Button
from systems.settings_panel import SettingsPanel
from systems.starfield import Starfield
from systems.tween import ease_out
from systems.game_state import GameState
from systems.crash_intro import CrashIntro


# Title screen: animated planet, starfield and Start/Settings/Quit buttons.
class TitleScene(Scene):
    music = "title"

    def __init__(self, game):
        super().__init__(game)
        title_font = pygame.font.Font(FONT_PATH, TITLE_FONT_SIZE)
        button_font = pygame.font.Font(FONT_PATH, BUTTON_FONT_SIZE)

        self.title_text = title_font.render("M24", False, TEXT_COLOR)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 5))

        # Buttons are stacked vertically, one button height + gap apart.
        center_x = SCREEN_WIDTH // 2
        first_y = 352
        step_y = BUTTON_HEIGHT + BUTTON_GAP
        self.start_button = Button("Start", (center_x, first_y), button_font)
        self.settings_button = Button("Settings", (center_x, first_y + step_y), button_font)
        self.quit_button = Button("Quit", (center_x, first_y + step_y * 2), button_font)
        self.buttons = [self.start_button, self.settings_button, self.quit_button]
        self.settings_panel = SettingsPanel(game)

        planet_sprite = pygame.image.load(PLANET_IMAGE_PATH).convert_alpha()
        planet_size = (planet_sprite.get_width() * PLANET_SCALE,
                       planet_sprite.get_height() * PLANET_SCALE)
        self.planet = pygame.transform.scale(planet_sprite, planet_size)
        self.planet_image = self.planet
        # The planet starts lower and slides up into place.
        self.planet_rect = self.planet.get_rect(
            center=(PLANET_CENTER[0], PLANET_CENTER[1] + PLANET_START_OFFSET))
        self.planet_timer = 0.0
        self.planet_bob_timer = 0.0

        # Stars are not placed on top of the title, buttons or planet.
        avoid_rects = [self.title_rect] + [button.rect for button in self.buttons]
        avoid_circles = [(PLANET_CENTER, PLANET_RADIUS)]
        self.starfield = Starfield(avoid_rects, avoid_circles)
        self.intro = None

    def handle_events(self, events):
        # While the crash intro plays, it gets all the input.
        if self.intro:
            self.intro.handle_events(events)
            return
        for event in events:
            if self.settings_panel.is_active():
                self.settings_panel.handle_event(event)
                continue
            start_clicked = self.start_button.handle_event(event)
            settings_clicked = self.settings_button.handle_event(event)
            quit_clicked = self.quit_button.handle_event(event)
            if start_clicked:
                # New game: fresh save state, forget old maps, play intro.
                self.game.play_sfx("select")
                self.game.state = GameState()
                self.game.overworlds = {}
                self.intro = CrashIntro(self)
                return
            elif settings_clicked:
                self.game.play_sfx("select")
                self.settings_panel.open()
            elif quit_clicked:
                self.game.play_sfx("select")
                self.game.running = False

    def update(self, dt):
        if self.intro:
            self.intro.update(dt)
            if self.intro.done:
                # Imported here (lazy import), only when the intro ends.
                from scenes.overworld_scene import OverworldScene
                self.game.scene = OverworldScene(self.game, from_crash=True)
                self.game.play_scene_music()
            return

        mouse_pos = pygame.mouse.get_pos()
        # Off-screen mouse position stops hover while a panel/transition is up.
        blocked = self.settings_panel.is_active() or self.game.curtain.is_busy()
        title_mouse_pos = (-1, -1) if blocked else mouse_pos
        for button in self.buttons:
            if button.update(title_mouse_pos):
                self.game.play_sfx("hover")
        self.starfield.update(dt)

        if not self.game.curtain.is_busy() and self.planet_timer < PLANET_INTRO_TIME:
            # Intro: ease the planet up from its start offset to its center.
            self.planet_timer = min(self.planet_timer + dt, PLANET_INTRO_TIME)
            remaining = 1 - ease_out(self.planet_timer / PLANET_INTRO_TIME, PLANET_EASE)
            center = (PLANET_CENTER[0], PLANET_CENTER[1] + PLANET_START_OFFSET * remaining)
            self.planet_rect = self.planet_image.get_rect(center=center)
        elif self.planet_timer >= PLANET_INTRO_TIME:
            # After the intro: bob up and down on a sine wave.
            self.planet_bob_timer += dt
            angle = self.planet_bob_timer * 2 * math.pi / PLANET_BOB_PERIOD
            bob = PLANET_BOB_AMPLITUDE * math.sin(angle)
            self.planet_rect.centery = round(PLANET_CENTER[1] + bob)
        self.settings_panel.update(dt, mouse_pos)

    def draw(self, screen):
        if self.intro:
            self.intro.draw(screen)
            return
        screen.fill(TITLE_BG_COLOR)
        self.starfield.draw(screen)
        screen.blit(self.planet_image, self.planet_rect)
        screen.blit(self.title_text, self.title_rect)
        for button in self.buttons:
            button.draw(screen)
        self.settings_panel.draw(screen)
