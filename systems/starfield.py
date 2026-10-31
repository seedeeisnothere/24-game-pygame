import random
import pygame
from settings import *


class Star:
    def __init__(self, x, y, brightness):
        self.x = x
        self.y = y
        background = pygame.Color(TITLE_BG_COLOR)
        star_color = pygame.Color(STAR_COLOR)
        self.colors = [background.lerp(star_color, brightness * level) for level in STAR_LEVELS]
        self.step = 0
        self.timer = random.uniform(0, STAR_WAIT_MAX)

    def update(self, dt):
        self.timer -= dt
        if self.timer > 0:
            return
        self.step = (self.step + 1) % len(STAR_LEVELS)
        if self.step == 0:
            self.timer = random.uniform(STAR_WAIT_MIN, STAR_WAIT_MAX)
        else:
            self.timer = STAR_STEP_TIME

    def draw(self, screen):
        pygame.draw.circle(screen, self.colors[self.step], (self.x, self.y), STAR_RADIUS)


class Starfield:
    def __init__(self, avoid_rects, avoid_circles):
        self.stars = []
        self.avoid_rects = [rect.inflate(STAR_CLEARANCE * 2, STAR_CLEARANCE * 2) for rect in avoid_rects]
        self.avoid_circles = [(center, radius + STAR_CLEARANCE) for center, radius in avoid_circles]
        tries = 0
        while tries < STAR_MAX_TRIES:
            tries += 1
            x = random.randint(STAR_MARGIN, SCREEN_WIDTH - STAR_MARGIN)
            y = random.randint(STAR_MARGIN, SCREEN_HEIGHT - STAR_MARGIN)
            if self.is_free(x, y):
                brightness = random.uniform(STAR_BRIGHTNESS_MIN, 1)
                self.stars.append(Star(x, y, brightness))

    def is_free(self, x, y):
        for rect in self.avoid_rects:
            if rect.collidepoint(x, y):
                return False
        for center, radius in self.avoid_circles:
            if (center[0] - x) ** 2 + (center[1] - y) ** 2 < radius ** 2:
                return False
        for star in self.stars:
            if (star.x - x) ** 2 + (star.y - y) ** 2 < STAR_MIN_DISTANCE ** 2:
                return False
        return True

    def update(self, dt):
        for star in self.stars:
            star.update(dt)

    def draw(self, screen):
        for star in self.stars:
            star.draw(screen)