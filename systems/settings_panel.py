import pygame
from settings import *
from systems.tween import ease_out, ease_in
from systems.ui import Button, HomeButton, Slider


# Full-screen settings/credits panel that slides in from the right.
# States: "hidden" -> "sliding_in" -> "shown" -> "sliding_out" -> "hidden"
class SettingsPanel:
    def __init__(self, game, in_game=False):
        self.game = game
        self.surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.state = "hidden"
        self.timer = 0.0
        self.x = SCREEN_WIDTH
        # Left half is settings, right half is credits
        self.half = SCREEN_WIDTH // 2

        big_font = pygame.font.Font(FONT_PATH, BUTTON_FONT_SIZE)
        small_font = pygame.font.Font(FONT_PATH, SMALL_FONT_SIZE)
        credits_font = pygame.font.Font(FONT_PATH, CREDITS_FONT_SIZE)

        self.settings_heading = big_font.render("Settings", False, TEXT_COLOR)
        self.settings_heading_rect = self.settings_heading.get_rect(
            topleft=(PANEL_MARGIN, PANEL_MARGIN))
        self.credits_heading = big_font.render("Credits", False, TEXT_COLOR)
        self.credits_heading_rect = self.credits_heading.get_rect(
            topleft=(self.half + PANEL_MARGIN, PANEL_MARGIN))

        # Pre-render each credits line with its position
        self.credits = []
        line_y = CREDITS_FIRST_Y
        for line in CREDITS_LINES:
            text = credits_font.render(line, False, TEXT_COLOR)
            rect = text.get_rect(topleft=(self.half + PANEL_MARGIN, line_y))
            self.credits.append((text, rect))
            line_y += CREDITS_LINE_HEIGHT

        self.sfx_slider = Slider("SFX", PANEL_MARGIN, SLIDER_FIRST_Y, game.sfx_volume, small_font)
        self.bgm_slider = Slider("BGM", PANEL_MARGIN, SLIDER_FIRST_Y + SLIDER_SPACING,
                                 game.bgm_volume, small_font)

        # Bottom button row. In-game, the Back button shrinks to fit a Home button.
        row_y = SCREEN_HEIGHT - PANEL_MARGIN - BUTTON_HEIGHT // 2
        back_width = BUTTON_WIDTH
        self.title_button = None
        if in_game:
            back_width = BUTTON_WIDTH - BUTTON_GAP - HOME_BUTTON_RADIUS * 2
            home_center = (PANEL_MARGIN + BUTTON_WIDTH - HOME_BUTTON_RADIUS, row_y)
            self.title_button = HomeButton(home_center)
        back_center = (PANEL_MARGIN + back_width // 2, row_y)
        self.back_button = Button("Back", back_center, big_font, back_width)
        self.buttons = [self.back_button]
        if self.title_button is not None:
            self.buttons.append(self.title_button)

    # Start sliding in (only if fully hidden).
    def open(self):
        if self.state == "hidden":
            self.state = "sliding_in"
            self.timer = 0.0
            for button in self.buttons:
                button.hovered = False

    # Start sliding out (only if fully shown).
    def close(self):
        if self.state == "shown":
            self.state = "sliding_out"
            self.timer = 0.0

    def is_active(self):
        return self.state != "hidden"

    # Handle sliders and buttons. Only works when the panel is fully shown.
    def handle_event(self, event):
        if self.state != "shown":
            return
        sfx_released = self.sfx_slider.handle_event(event)
        self.bgm_slider.handle_event(event)
        self.game.sfx_volume = self.sfx_slider.value
        self.game.bgm_volume = self.bgm_slider.value
        self.game.music.set_volume(self.game.bgm_volume)
        # Play a sample sound when the SFX slider is let go
        if sfx_released:
            self.game.play_sfx("select")
        if self.back_button.handle_event(event):
            self.game.play_sfx("select")
            self.close()
        if self.title_button is not None and self.title_button.handle_event(event):
            self.game.play_sfx("select")
            self.game.change_scene("title")

    # Move the panel during slide animations, or update button hover.
    def update(self, dt, mouse_pos):
        if self.state == "sliding_in":
            self.timer += dt
            progress = min(self.timer / PANEL_SLIDE_TIME, 1)
            # x goes from SCREEN_WIDTH (off-screen right) to 0
            self.x = SCREEN_WIDTH * (1 - ease_out(progress))
            if progress >= 1:
                self.state = "shown"
        elif self.state == "shown":
            # Fake an off-screen mouse while the curtain is moving, so nothing hovers
            panel_mouse_pos = (-1, -1) if self.game.curtain.is_busy() else mouse_pos
            for button in self.buttons:
                if button.update(panel_mouse_pos):
                    self.game.play_sfx("hover")
        elif self.state == "sliding_out":
            self.timer += dt
            progress = min(self.timer / PANEL_SLIDE_TIME, 1)
            # x goes from 0 back to SCREEN_WIDTH
            self.x = SCREEN_WIDTH * ease_in(progress)
            if progress >= 1:
                self.state = "hidden"

    # Draw everything onto the panel surface, then blit it at self.x.
    def draw(self, screen):
        if self.state == "hidden":
            return
        self.surface.fill(PANEL_COLOR)
        self.surface.blit(self.settings_heading, self.settings_heading_rect)
        self.surface.blit(self.credits_heading, self.credits_heading_rect)
        # Vertical divider between the two halves
        pygame.draw.line(self.surface, SLIDER_TRACK_COLOR, (self.half, PANEL_MARGIN),
                         (self.half, SCREEN_HEIGHT - PANEL_MARGIN), 2)
        self.sfx_slider.draw(self.surface)
        self.bgm_slider.draw(self.surface)
        for text, rect in self.credits:
            self.surface.blit(text, rect)
        for button in self.buttons:
            button.draw(self.surface)
        screen.blit(self.surface, (int(self.x), 0))
