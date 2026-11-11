import pygame
from settings import *
from systems.tween import ease_out, ease_in


# Scene-change curtain that slides in from the right and out to the left.
# States: "idle" -> "closing" -> "covered" -> "holding" -> "opening" -> "idle"
class Curtain:
    def __init__(self):
        self.surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.surface.fill(CURTAIN_COLOR)
        self.state = "idle"
        self.timer = 0.0
        self.x = SCREEN_WIDTH

    # Begin covering the screen.
    def start(self):
        self.state = "closing"
        self.timer = 0.0
        self.x = SCREEN_WIDTH

    # Called once the new scene is loaded; wait a moment, then open.
    def finish_loading(self):
        self.state = "holding"
        self.timer = 0.0

    def is_busy(self):
        return self.state != "idle"

    # Advance the animation. "covered" waits until finish_loading() is called.
    def update(self, dt):
        if self.state == "closing":
            self.timer += dt
            progress = min(self.timer / CURTAIN_SLIDE_TIME, 1)
            # x goes from SCREEN_WIDTH to 0 (slides in from the right)
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
            # x goes from 0 to -SCREEN_WIDTH (slides out to the left)
            self.x = -SCREEN_WIDTH * ease_in(progress)
            if progress >= 1:
                self.state = "idle"

    def draw(self, screen):
        if self.state == "idle":
            return
        screen.blit(self.surface, (int(self.x), 0))
