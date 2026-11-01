import pygame
from settings import *
from systems.tween import ease_out, ease_in


class Curtain:
    def __init__(self):
        self.surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.surface.fill(CURTAIN_COLOR)
        self.state = "idle"
        self.timer = 0.0
        self.x = SCREEN_WIDTH

    def start(self):
        self.state = "closing"
        self.timer = 0.0
        self.x = SCREEN_WIDTH

    def finish_loading(self):
        self.state = "holding"
        self.timer = 0.0

    def is_busy(self):
        return self.state != "idle"

    def update(self, dt):
        if self.state == "closing":
            self.timer += dt
            progress = min(self.timer / CURTAIN_SLIDE_TIME, 1)
            self.x = SCREEN_WIDTH * (1 - ease_out(progress))
            if progress >= 1:
                self.state = "covered"
        elif self.state == "holding":
            self.timer += dt
            if self.timer >= CURTAIN_HOLD_TIME:
                self.state = "opening"
                self.timer = 0.0
        elif self.state == "opening":
            self.timer += dt
            progress = min(self.timer / CURTAIN_SLIDE_TIME, 1)
            self.x = -SCREEN_WIDTH * ease_in(progress)
            if progress >= 1:
                self.state = "idle"

    def draw(self, screen):
        if self.state == "idle":
            return
        screen.blit(self.surface, (int(self.x), 0))