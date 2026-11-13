import math
import pygame
from settings import *
from scenes.scene import Scene
from systems.ui import Button
from systems.starfield import Starfield
from systems.tween import ease_in, ease_out
from systems.crash_intro import (SHIP_FRAME_PATHS, SHIP_FRAME_TIME, PLANET_BODY_RADIUS,
                                 IMPACT_ANGLE, bezier, bezier_tangent, phase)

# Timeline, in seconds after the scene starts
LIFTOFF_START = 0.8
FLIGHT_TIME = 3.2
THE_END_START = LIFTOFF_START + FLIGHT_TIME + 0.4
THE_END_FADE = 1.2
BUTTON_START = THE_END_START + THE_END_FADE

SHIP_START_SCALE = 1.4
SHIP_END_SCALE = 3.2
# Flies out the way it came in: up and off the top-left of the screen
SHIP_CURVE = (SCREEN_WIDTH * 0.3, SCREEN_HEIGHT * 0.12)
SHIP_EXIT = (-120, -160)
TRAIL_INTERVAL = 0.03
TRAIL_LIFE = 0.8
FADE_IN_TIME = 1.0          # fade in from black (after the ship repair)


# Ending: the fixed ship lifts off the planet and flies home, then "THE END".
class EndScene(Scene):
    music = "ending"

    def __init__(self, game, fade_in=False):
        super().__init__(game)
        self.black = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.fade_in = FADE_IN_TIME if fade_in else 0.0
        planet = pygame.image.load(PLANET_IMAGE_PATH).convert_alpha()
        size = (planet.get_width() * PLANET_SCALE, planet.get_height() * PLANET_SCALE)
        self.planet = pygame.transform.scale(planet, size)
        self.planet_rect = self.planet.get_rect(center=PLANET_CENTER)
        self.starfield = Starfield([], [(PLANET_CENTER, PLANET_RADIUS)])
        self.frames = [pygame.image.load(path).convert_alpha() for path in SHIP_FRAME_PATHS]

        # Take off from the same spot it crashed into
        radius = PLANET_BODY_RADIUS * PLANET_SCALE
        self.start = (PLANET_CENTER[0] + math.cos(IMPACT_ANGLE) * radius,
                      PLANET_CENTER[1] + math.sin(IMPACT_ANGLE) * radius)
        self.ship_pos = self.start
        self.ship_angle = 0.0
        self.ship_scale = SHIP_START_SCALE
        self.trail = []             # each puff is [x, y, age]
        self.trail_timer = 0.0
        self.time = 0.0

        title_font = pygame.font.Font(FONT_PATH, TITLE_FONT_SIZE)
        small_font = pygame.font.Font(FONT_PATH, SMALL_FONT_SIZE)
        self.the_end = title_font.render("THE END", False, TEXT_COLOR)
        self.the_end_rect = self.the_end.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3))
        self.thanks = small_font.render("John made it home. Thanks for playing!", False, TEXT_COLOR)
        self.thanks_rect = self.thanks.get_rect(midtop=(SCREEN_WIDTH // 2, self.the_end_rect.bottom + 16))
        button_font = pygame.font.Font(FONT_PATH, BUTTON_FONT_SIZE)
        self.button = Button("Title", (SCREEN_WIDTH // 2, SCREEN_HEIGHT * 2 // 3), button_font)

    def handle_events(self, events):
        if self.time < BUTTON_START:
            return
        for event in events:
            if self.button.handle_event(event):
                self.game.play_sfx("select")
                self.game.change_scene("title")

    def update(self, dt):
        self.time += dt
        self.fade_in = max(0.0, self.fade_in - dt)
        self.starfield.update(dt)

        flight = phase(self.time, LIFTOFF_START, FLIGHT_TIME)
        if 0 < flight < 1:
            t = ease_in(flight, 1.6)        # slow lift-off, then speeds away
            self.ship_pos = bezier(self.start, SHIP_CURVE, SHIP_EXIT, t)
            dx, dy = bezier_tangent(self.start, SHIP_CURVE, SHIP_EXIT, t)
            self.ship_angle = math.degrees(math.atan2(-dy, dx)) - 90
            self.ship_scale = SHIP_START_SCALE + (SHIP_END_SCALE - SHIP_START_SCALE) * t
            self.trail_timer -= dt
            if self.trail_timer <= 0:
                self.trail_timer = TRAIL_INTERVAL
                self.trail.append([self.ship_pos[0], self.ship_pos[1], 0.0])
        for puff in self.trail:
            puff[2] += dt
        self.trail = [puff for puff in self.trail if puff[2] < TRAIL_LIFE]

        if self.time >= BUTTON_START:
            blocked = self.game.curtain.is_busy()
            if self.button.update((-1, -1) if blocked else pygame.mouse.get_pos()):
                self.game.play_sfx("hover")

    def draw(self, screen):
        screen.fill(TITLE_BG_COLOR)
        self.starfield.draw(screen)
        screen.blit(self.planet, self.planet_rect)

        # Exhaust trail: newer puffs are small and bright, older ones fade
        for x, y, age in self.trail:
            life = age / TRAIL_LIFE
            radius = round(3 + 9 * life)
            shade = round(230 - 150 * life)
            pygame.draw.circle(screen, (shade, shade - 40, 80), (x, y), radius)

        if self.time < LIFTOFF_START + FLIGHT_TIME:
            if self.time < LIFTOFF_START:
                frame = self.frames[0]
            else:
                frame = self.frames[int(self.time / SHIP_FRAME_TIME) % len(self.frames)]
            size = round(frame.get_width() * self.ship_scale)
            ship = pygame.transform.rotate(pygame.transform.scale(frame, (size, size)), self.ship_angle)
            screen.blit(ship, ship.get_rect(center=self.ship_pos))

        fade = phase(self.time, THE_END_START, THE_END_FADE)
        if fade > 0:
            alpha = round(255 * ease_out(fade, 2))
            self.the_end.set_alpha(alpha)
            self.thanks.set_alpha(alpha)
            screen.blit(self.the_end, self.the_end_rect)
            screen.blit(self.thanks, self.thanks_rect)
        if self.time >= BUTTON_START:
            self.button.draw(screen)
        if self.fade_in > 0:
            self.black.set_alpha(round(255 * self.fade_in / FADE_IN_TIME))
            screen.blit(self.black, (0, 0))
