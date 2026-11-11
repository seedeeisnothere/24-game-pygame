import pygame
from settings import *
from scenes.scene import Scene
from systems.ui import Button


# Game over screen with a single button back to the title.
class GameOverScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        title_font = pygame.font.Font(FONT_PATH, TITLE_FONT_SIZE)
        button_font = pygame.font.Font(FONT_PATH, BUTTON_FONT_SIZE)
        self.heading = title_font.render("Game Over", False, TEXT_COLOR)
        self.heading_rect = self.heading.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        self.button = Button("Title", (SCREEN_WIDTH // 2, SCREEN_HEIGHT * 2 // 3), button_font)

    def handle_events(self, events):
        for event in events:
            if self.button.handle_event(event):
                self.game.play_sfx("select")
                self.game.change_scene("title")

    def update(self, dt):
        # During a scene transition, use an off-screen mouse so nothing hovers.
        blocked = self.game.curtain.is_busy()
        mouse_pos = (-1, -1) if blocked else pygame.mouse.get_pos()
        if self.button.update(mouse_pos):
            self.game.play_sfx("hover")

    def draw(self, screen):
        screen.fill(TITLE_BG_COLOR)
        screen.blit(self.heading, self.heading_rect)
        self.button.draw(screen)
