import pygame
from settings import *
from scenes.scene import Scene
from systems.ui import Button
from systems.settings_panel import SettingsPanel
from systems.starfield import Starfield
from systems.tween import ease_out


class TitleScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        title_font = pygame.font.Font(FONT_PATH, TITLE_FONT_SIZE)
        button_font = pygame.font.Font(FONT_PATH, BUTTON_FONT_SIZE)

        self.title_text = title_font.render("M24", False, TEXT_COLOR)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 5))


        center_x = SCREEN_WIDTH // 2
        first_y = 352
        step_y = BUTTON_HEIGHT + BUTTON_GAP
        self.start_button = Button("Start", (center_x, first_y), button_font)
        self.settings_button = Button("Settings", (center_x, first_y + step_y), button_font)
        self.quit_button = Button("Quit", (center_x, first_y + step_y * 2), button_font)
        self.buttons = [self.start_button, self.settings_button, self.quit_button]
        self.settings_panel = SettingsPanel(game)
        self.planet = pygame.Surface((PLANET_RADIUS * 2, PLANET_RADIUS * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.planet, PLANET_COLOR, (PLANET_RADIUS, PLANET_RADIUS), PLANET_RADIUS)
        for position, radius in PLANET_SPOTS:
            pygame.draw.circle(self.planet, PLANET_SPOT_COLOR, position, radius)
        self.planet_image = self.planet
        self.planet_rect = self.planet.get_rect(center=PLANET_CENTER)
        self.planet_timer = 0.0
        avoid_rects = [self.title_rect] + [button.rect for button in self.buttons]
        avoid_circles = [(PLANET_CENTER, PLANET_RADIUS)]
        self.starfield = Starfield(avoid_rects, avoid_circles)

    def handle_events(self, events):
        for event in events:
            if self.settings_panel.is_active():
                self.settings_panel.handle_event(event)
                continue
            start_clicked = self.start_button.handle_event(event)
            settings_clicked = self.settings_button.handle_event(event)
            quit_clicked = self.quit_button.handle_event(event)
            if start_clicked:
                self.game.change_scene("overworld")
            elif settings_clicked:
                self.settings_panel.open()
            elif quit_clicked:
                self.game.running = False

    def update(self, dt):
        mouse_pos = pygame.mouse.get_pos()
        title_mouse_pos = (-1, -1) if self.settings_panel.is_active() else mouse_pos
        for button in self.buttons:
            button.update(title_mouse_pos)
        self.starfield.update(dt)
        if self.planet_timer < PLANET_INTRO_TIME:
            self.planet_timer = min(self.planet_timer + dt, PLANET_INTRO_TIME)
            remaining = 1 - ease_out(self.planet_timer / PLANET_INTRO_TIME, PLANET_EASE)
            self.planet_image = pygame.transform.rotate(self.planet, PLANET_SPIN_DEGREES * remaining)
            center = (PLANET_CENTER[0], PLANET_CENTER[1] + PLANET_START_OFFSET * remaining)
            self.planet_rect = self.planet_image.get_rect(center=center)
        self.settings_panel.update(dt, mouse_pos)

    def draw(self, screen):
        screen.fill(TITLE_BG_COLOR)
        self.starfield.draw(screen)
        screen.blit(self.planet_image, self.planet_rect)
        screen.blit(self.title_text, self.title_rect)
        for button in self.buttons:
            button.draw(screen)
        self.settings_panel.draw(screen)