import math
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

# Points the way to the current objective:
#   off screen -> a red triangle circling the player, pointing at it
#   on screen  -> a bobbing red dot above it, with a pulsing ring
MARKER_COLOR = (230, 45, 45)
MARKER_OUTLINE = (40, 8, 8)
ORBIT_RADIUS = 70           # triangle's distance from the player's center
TRIANGLE_SIZE = 24          # tip to back of the triangle
TRIANGLE_HALF_WIDTH = 7
DOT_RADIUS = 8
DOT_GAP = 18                # dot sits this far above the target's top
BOB_PX = 5                  # how far the dot bobs up and down
BOB_SPEED = 4.0             # radians per second
PULSE_TIME = 1.1            # seconds per ring pulse
PULSE_GROW = 16             # ring grows this much past the dot


# True if a screen point is inside the screen.
def on_screen(point, size=(SCREEN_WIDTH, SCREEN_HEIGHT)):
    return 0 <= point[0] <= size[0] and 0 <= point[1] <= size[1]


# Where the triangle goes: on a circle around the player, on the side facing
# the target (both in screen coordinates). Returns (x, y, angle).
def orbit_point(player, target, radius=ORBIT_RADIUS):
    angle = math.atan2(target[1] - player[1], target[0] - player[0])
    return (player[0] + math.cos(angle) * radius,
            player[1] + math.sin(angle) * radius, angle)


class ObjectiveMarker:
    def __init__(self):
        self.time = 0.0
        ring_size = (DOT_RADIUS + PULSE_GROW) * 2 + 4
        self.ring = pygame.Surface((ring_size, ring_size), pygame.SRCALPHA)

    # target: the objective's world rect (None = nothing to point at).
    # player: the player's center in world coordinates.
    def draw(self, screen, target, player, cam_x, cam_y, dt):
        self.time += dt
        if target is None:
            return
        anchor = (target.centerx - cam_x, target.top - cam_y)
        # Center decides on/off screen; a dot whose spot is above the top is clamped down.
        center = (target.centerx - cam_x, target.centery - cam_y)
        if not on_screen(center):
            player = (player[0] - cam_x, player[1] - cam_y)
            self.draw_triangle(screen, *orbit_point(player, center))
        else:
            x = anchor[0]
            y = max(DOT_RADIUS + BOB_PX, anchor[1] - DOT_GAP)
            self.draw_dot(screen, x, y)

    def draw_triangle(self, screen, x, y, angle):
        # Gentle nudge toward the target so it catches the eye.
        nudge = 3 * math.sin(self.time * BOB_SPEED)
        x += math.cos(angle) * nudge
        y += math.sin(angle) * nudge
        cos, sin = math.cos(angle), math.sin(angle)
        tip = (x + cos * TRIANGLE_SIZE / 2, y + sin * TRIANGLE_SIZE / 2)
        back_x, back_y = x - cos * TRIANGLE_SIZE / 2, y - sin * TRIANGLE_SIZE / 2
        left = (back_x - sin * TRIANGLE_HALF_WIDTH, back_y + cos * TRIANGLE_HALF_WIDTH)
        right = (back_x + sin * TRIANGLE_HALF_WIDTH, back_y - cos * TRIANGLE_HALF_WIDTH)
        points = [tip, left, right]
        pygame.draw.polygon(screen, MARKER_COLOR, points)
        pygame.draw.polygon(screen, MARKER_OUTLINE, points, 2)

    def draw_dot(self, screen, x, y):
        y += math.sin(self.time * BOB_SPEED) * BOB_PX
        # Expanding ring that fades out, restarting every PULSE_TIME.
        t = (self.time % PULSE_TIME) / PULSE_TIME
        self.ring.fill((0, 0, 0, 0))
        center = self.ring.get_width() // 2
        radius = round(DOT_RADIUS + PULSE_GROW * t)
        alpha = round(255 * (1 - t) ** 0.6)
        pygame.draw.circle(self.ring, (*MARKER_COLOR, alpha), (center, center), radius, 3)
        screen.blit(self.ring, (round(x) - center, round(y) - center))
        # The dot itself, slightly bigger at the start of each pulse.
        r = DOT_RADIUS + (2 if t < 0.15 else 0)
        pygame.draw.circle(screen, MARKER_OUTLINE, (round(x), round(y)), r + 2)
        pygame.draw.circle(screen, MARKER_COLOR, (round(x), round(y)), r)
        pygame.draw.circle(screen, (255, 170, 170), (round(x) - 2, round(y) - 2), 2)
