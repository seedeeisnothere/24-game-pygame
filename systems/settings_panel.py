import pygame
from settings import *
from systems.tween import ease_out, ease_in
from systems.ui import Button, Slider


class SettingsPanel:
    def __init__(self, game):
        self.game = game
        self.surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.state = "hidden"
        self.timer = 0.0
        self.x = SCREEN_WIDTH
        self.half = SCREEN_WIDTH // 2

        big_font = pygame.font.Font(FONT_PATH, BUTTON_FONT_SIZE)
        small_font = pygame.font.Font(FONT_PATH, SMALL_FONT_SIZE)
        credits_font = pygame.font.Font(FONT_PATH, CREDITS_FONT_SIZE)

        self.settings_heading = big_font.render("Settings", False, TEXT_COLOR)
        self.settings_heading_rect = self.settings_heading.get_rect(topleft=(PANEL_MARGIN, PANEL_MARGIN))
        self.credits_heading = big_font.render("Credits", False, TEXT_COLOR)
        self.credits_heading_rect = self.credits_heading.get_rect(topleft=(self.half + PANEL_MARGIN, PANEL_MARGIN))

        self.credits = []
        line_y = CREDITS_FIRST_Y
        for line in CREDITS_LINES:
            text = credits_font.render(line, False, TEXT_COLOR)
            rect = text.get_rect(topleft=(self.half + PANEL_MARGIN, line_y))
            self.credits.append((text, rect))
            line_y += CREDITS_LINE_HEIGHT

        self.sfx_slider = Slider("SFX", PANEL_MARGIN, SLIDER_FIRST_Y, game.sfx_volume, small_font)
        self.bgm_slider = Slider("BGM", PANEL_MARGIN, SLIDER_FIRST_Y + SLIDER_SPACING, game.bgm_volume, small_font)
        back_center = (PANEL_MARGIN + BUTTON_WIDTH // 2, SCREEN_HEIGHT - PANEL_MARGIN - BUTTON_HEIGHT // 2)
        self.back_button = Button("Back", back_center, big_font)

    def open(self):
        if self.state == "hidden":
            self.state = "sliding_in"
            self.timer = 0.0
            self.back_button.hovered = False

    def close(self):
        if self.state == "shown":
            self.state = "sliding_out"
            self.timer = 0.0

    def is_active(self):
        return self.state != "hidden"

    def handle_event(self, event):
        if self.state != "shown":
            return
        self.sfx_slider.handle_event(event)
        self.bgm_slider.handle_event(event)
        self.game.sfx_volume = self.sfx_slider.value
        self.game.bgm_volume = self.bgm_slider.value
        if self.back_button.handle_event(event):
            self.close()

    def update(self, dt, mouse_pos):
        if self.state == "sliding_in":
            self.timer += dt
            progress = min(self.timer / PANEL_SLIDE_TIME, 1)
            self.x = SCREEN_WIDTH * (1 - ease_out(progress))
            if progress >= 1:
                self.state = "shown"
        elif self.state == "shown":
            self.back_button.update(mouse_pos)
        elif self.state == "sliding_out":
            self.timer += dt
            progress = min(self.timer / PANEL_SLIDE_TIME, 1)
            self.x = SCREEN_WIDTH * ease_in(progress)
            if progress >= 1:
                self.state = "hidden"

    def draw(self, screen):
        if self.state == "hidden":
            return
        self.surface.fill(PANEL_COLOR)
        self.surface.blit(self.settings_heading, self.settings_heading_rect)
        self.surface.blit(self.credits_heading, self.credits_heading_rect)
        pygame.draw.line(self.surface, SLIDER_TRACK_COLOR, (self.half, PANEL_MARGIN), (self.half, SCREEN_HEIGHT - PANEL_MARGIN), 2)
        self.sfx_slider.draw(self.surface)
        self.bgm_slider.draw(self.surface)
        for text, rect in self.credits:
            self.surface.blit(text, rect)
        self.back_button.draw(self.surface)
        screen.blit(self.surface, (int(self.x), 0))