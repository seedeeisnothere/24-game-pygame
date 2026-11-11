import math
import random
import pygame
from settings import *
from systems.starfield import Star
from systems.tween import ease_in

SHIP_FRAME_PATHS = [f"assets/sprites/spaceship/fly_{i}.png" for i in range(3)]
EXPLOSION_SFX_PATH = "assets/sfx/Explosion.wav"

# Timeline, in seconds after pressing Start
GUI_FADE_TIME = 0.35
ZOOM_START = 0.15
ZOOM_TIME = 1.3
# Zoom out to 70% size
ZOOM_TO = 0.7
FLIGHT_START = 1.0
FLIGHT_TIME = 2.6
IMPACT_TIME = FLIGHT_START + FLIGHT_TIME
# Screen starts turning white 1 second before impact
FLASH_START = IMPACT_TIME - 1.0
# Fully white 0.6 seconds after impact
FLASH_FULL = IMPACT_TIME + 0.6
# Hold the white screen a bit before the game starts
END_TIME = FLASH_FULL + 0.5

SHIP_FRAME_TIME = 0.07
SHIP_START_SCALE = 3.0
SHIP_END_SCALE = 1.6
# Ship enters from off-screen top-left
SHIP_START = (-60, -90)
# Bezier control point that bends the flight path
SHIP_CURVE = (SCREEN_WIDTH * 0.3, SCREEN_HEIGHT * 0.12)
# Planet radius inside the sprite, before scaling
PLANET_BODY_RADIUS = 19.5
# Crash point on the planet's edge (upper-left side)
IMPACT_ANGLE = math.radians(235)
SMOKE_INTERVAL = 0.025
SMOKE_LIFE = 0.7
SHAKE_TIME = 0.6
SHAKE_STRENGTH = 10


# Point on a quadratic Bezier curve at t (0 to 1)
def bezier(p0, p1, p2, t):
    u = 1 - t
    return (u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
            u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1])


# Direction of the Bezier curve at t (its derivative)
def bezier_tangent(p0, p1, p2, t):
    return (2 * (1 - t) * (p1[0] - p0[0]) + 2 * t * (p2[0] - p1[0]),
            2 * (1 - t) * (p1[1] - p0[1]) + 2 * t * (p2[1] - p1[1]))


# Progress (0 to 1) of a step that starts at start and lasts length
def phase(time, start, length):
    return max(0.0, min((time - start) / length, 1.0))


# Cutscene after Start: GUI fades, camera zooms out, ship crashes, white flash
class CrashIntro:

    def __init__(self, title):
        self.title = title
        self.game = title.game
        self.time = 0.0
        self.done = False
        self.impacted = False
        # Zoom happens around the screen centre
        self.pivot = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.planet_center = title.planet_rect.center
        self.zoom = 1.0
        # (size, scaled image) so the planet is only rescaled when size changes
        self.planet_cache = (None, None)

        self.frames = [pygame.image.load(path).convert_alpha() for path in SHIP_FRAME_PATHS]
        self.explosion = pygame.mixer.Sound(EXPLOSION_SFX_PATH)
        self.white = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.white.fill("#FFFFFF")
        self.gui_layer = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.world = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        # Crash point uses where the planet will be after zooming out
        final_center = self.to_screen(self.planet_center, ZOOM_TO)
        radius = PLANET_BODY_RADIUS * PLANET_SCALE * ZOOM_TO
        self.impact = (final_center[0] + math.cos(IMPACT_ANGLE) * radius,
                       final_center[1] + math.sin(IMPACT_ANGLE) * radius)

        self.ship_pos = SHIP_START
        self.ship_angle = 0.0
        self.ship_scale = SHIP_START_SCALE
        # Each puff is [x, y, age]
        self.smoke = []
        self.smoke_timer = 0.0
        self.extra_stars = self.make_outer_stars()

    # Apply the zoom around the pivot to a point
    def to_screen(self, point, zoom=None):
        zoom = self.zoom if zoom is None else zoom
        return (self.pivot[0] + (point[0] - self.pivot[0]) * zoom,
                self.pivot[1] + (point[1] - self.pivot[1]) * zoom)

    # Make stars outside the screen so edges aren't empty after zooming out
    def make_outer_stars(self):
        # Area visible when fully zoomed out
        half_w = SCREEN_WIDTH / 2 / ZOOM_TO
        half_h = SCREEN_HEIGHT / 2 / ZOOM_TO
        left, right = int(self.pivot[0] - half_w), int(self.pivot[0] + half_w)
        top, bottom = int(self.pivot[1] - half_h), int(self.pivot[1] + half_h)
        screen = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        taken = [(star.x, star.y) for star in self.title.starfield.stars]
        planet_radius = PLANET_RADIUS + STAR_CLEARANCE
        stars = []
        # Try random spots; skip ones on screen, on the planet, or too close
        for _ in range(STAR_MAX_TRIES):
            x, y = random.randint(left, right), random.randint(top, bottom)
            if screen.collidepoint(x, y):
                continue
            if math.dist((x, y), self.planet_center) < planet_radius:
                continue
            if any(math.dist((x, y), other) < STAR_MIN_DISTANCE for other in taken):
                continue
            taken.append((x, y))
            stars.append(Star(x, y, random.uniform(STAR_BRIGHTNESS_MIN, 1)))
        return stars

    # Jump almost to the end of the cutscene
    def skip(self):
        self.time = max(self.time, FLASH_FULL - 0.3)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN):
                self.skip()

    # Move the cutscene forward by dt seconds
    def update(self, dt):
        self.time += dt
        for star in self.title.starfield.stars + self.extra_stars:
            star.update(dt)

        # Ease in-out: slow start, fast middle, slow end
        zoom_t = phase(self.time, ZOOM_START, ZOOM_TIME)
        eased = ease_in(zoom_t * 2, 2) / 2 if zoom_t < 0.5 else 1 - ease_in((1 - zoom_t) * 2, 2) / 2
        self.zoom = 1 + (ZOOM_TO - 1) * eased

        flight_t = phase(self.time, FLIGHT_START, FLIGHT_TIME)
        if 0 < flight_t < 1:
            # Ship speeds up as it gets closer to the planet
            t = ease_in(flight_t, 1.5)
            self.ship_pos = bezier(SHIP_START, SHIP_CURVE, self.impact, t)
            # Point the ship along the path (-dy because screen y goes down)
            dx, dy = bezier_tangent(SHIP_START, SHIP_CURVE, self.impact, t)
            self.ship_angle = math.degrees(math.atan2(-dy, dx)) - 90
            self.ship_scale = SHIP_START_SCALE + (SHIP_END_SCALE - SHIP_START_SCALE) * t
            # Drop a smoke puff every SMOKE_INTERVAL seconds
            self.smoke_timer -= dt
            if self.smoke_timer <= 0:
                self.smoke_timer = SMOKE_INTERVAL
                self.smoke.append([self.ship_pos[0], self.ship_pos[1], 0.0])

        # Age smoke puffs and remove old ones
        for puff in self.smoke:
            puff[2] += dt
        self.smoke = [puff for puff in self.smoke if puff[2] < SMOKE_LIFE]

        # Play the explosion sound once at impact
        if not self.impacted and self.time >= IMPACT_TIME:
            self.impacted = True
            self.explosion.set_volume(self.game.sfx_volume)
            self.explosion.play()

        if self.time >= END_TIME:
            self.done = True

    # Return the planet image scaled to the current zoom
    def planet_surface(self):
        size = round(self.title.planet_image.get_width() * self.zoom)
        if self.planet_cache[0] != size:
            self.planet_cache = (size, pygame.transform.scale(self.title.planet_image, (size, size)))
        return self.planet_cache[1]

    # Draw stars, planet, smoke and ship onto a surface
    def draw_world(self, surface):
        surface.fill(TITLE_BG_COLOR)
        star_radius = max(2, round(STAR_RADIUS * self.zoom))
        for star in self.title.starfield.stars + self.extra_stars:
            pygame.draw.circle(surface, star.colors[star.step], self.to_screen((star.x, star.y)), star_radius)

        planet = self.planet_surface()
        surface.blit(planet, planet.get_rect(center=self.to_screen(self.planet_center)))

        # Older puffs are bigger and darker
        for x, y, age in self.smoke:
            life = age / SMOKE_LIFE
            radius = round(4 + 10 * life)
            shade = round(120 - 70 * life)
            pygame.draw.circle(surface, (shade, shade, shade + 10), (x, y), radius)

        if FLIGHT_START < self.time < IMPACT_TIME:
            # Loop through ship frames for animation
            frame = self.frames[int(self.time / SHIP_FRAME_TIME) % len(self.frames)]
            size = round(frame.get_width() * self.ship_scale)
            ship = pygame.transform.rotate(pygame.transform.scale(frame, (size, size)), self.ship_angle)
            surface.blit(ship, ship.get_rect(center=self.ship_pos))

    # Draw the title and buttons fading out
    def draw_gui(self, screen):
        alpha = round(255 * (1 - phase(self.time, 0, GUI_FADE_TIME)))
        if alpha <= 0:
            return
        self.gui_layer.fill((0, 0, 0, 0))
        self.gui_layer.blit(self.title.title_text, self.title.title_rect)
        for button in self.title.buttons:
            button.draw(self.gui_layer)
        self.gui_layer.set_alpha(alpha)
        screen.blit(self.gui_layer, (0, 0))

    # Draw the full cutscene frame with shake and white flash
    def draw(self, screen):
        self.draw_world(self.world)
        offset = (0, 0)
        # Screen shake after impact that fades out over SHAKE_TIME
        since_impact = self.time - IMPACT_TIME
        if 0 <= since_impact < SHAKE_TIME:
            strength = SHAKE_STRENGTH * (1 - since_impact / SHAKE_TIME)
            offset = (random.uniform(-strength, strength), random.uniform(-strength, strength))
        screen.fill(TITLE_BG_COLOR)
        screen.blit(self.world, offset)
        self.draw_gui(screen)

        # White overlay that fades in from FLASH_START to FLASH_FULL
        flash = phase(self.time, FLASH_START, FLASH_FULL - FLASH_START)
        if flash > 0:
            self.white.set_alpha(round(255 * ease_in(flash, 2)))
            screen.blit(self.white, (0, 0))
