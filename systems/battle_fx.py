import math
import random
import pygame
from systems.tween import ease_in, ease_out

# Battle animations: the enemy's attacks (slime tackle, boss beam) and the
# player's dodge hop / hurt shake. Each one is started, updated with dt and
# asked where things should be drawn; none of them deal damage themselves.
# Enemy attacks return "impact" from update() on the frame they would hit.


def clamp01(t):
    return max(0.0, min(1.0, t))


# --- Slime tackle -----------------------------------------------------------
TACKLE_WINDUP = 0.12        # squash down and lean back
TACKLE_LUNGE = 0.12         # dash at the player (impact at the end)
TACKLE_HOLD = 0.06          # stay pressed against the player
TACKLE_RETURN = 0.30        # hop back home
TACKLE_BACKUP = 26          # pixels the slime leans back before lunging
TACKLE_HOP = 40             # how high the slime arcs while lunging
TACKLE_TIME = TACKLE_WINDUP + TACKLE_LUNGE + TACKLE_HOLD + TACKLE_RETURN


class Tackle:
    # distance: how far left (in pixels) the enemy travels to reach the player.
    def __init__(self, distance):
        self.distance = distance
        self.timer = 0.0
        self.hit = False

    @property
    def done(self):
        return self.timer >= TACKLE_TIME

    def update(self, dt):
        self.timer += dt
        if not self.hit and self.timer >= TACKLE_WINDUP + TACKLE_LUNGE:
            self.hit = True
            return "impact"
        return None

    # Where the enemy is, as (dx, dy) from its resting spot.
    def offset(self):
        t = self.timer
        if t < TACKLE_WINDUP:
            return TACKLE_BACKUP * ease_out(t / TACKLE_WINDUP), 0
        t -= TACKLE_WINDUP
        if t < TACKLE_LUNGE:
            k = ease_in(t / TACKLE_LUNGE, 2)
            x = TACKLE_BACKUP + (-self.distance - TACKLE_BACKUP) * k
            return x, -math.sin(k * math.pi) * TACKLE_HOP
        t -= TACKLE_LUNGE
        if t < TACKLE_HOLD:
            return -self.distance, 0
        t -= TACKLE_HOLD
        k = ease_out(clamp01(t / TACKLE_RETURN))
        # Bounce back home in a small arc.
        return -self.distance * (1 - k), -math.sin(k * math.pi) * TACKLE_HOP * 0.6

    # Squash and stretch as (width, height) scale factors.
    def squash(self):
        t = self.timer
        if t < TACKLE_WINDUP:
            k = ease_out(t / TACKLE_WINDUP)
            return 1 + 0.18 * k, 1 - 0.18 * k
        t -= TACKLE_WINDUP
        if t < TACKLE_LUNGE:
            return 1.22, 0.86
        t -= TACKLE_LUNGE
        if t < TACKLE_HOLD:
            return 0.85, 1.12
        return 1.0, 1.0


# --- Boss beam --------------------------------------------------------------
BEAM_CHARGE = 0.12          # orb flares up in front of the boss
BEAM_FIRE = 0.30            # beam is on screen (impact when it starts)
BEAM_WIDTH = 36             # beam thickness at full power
BEAM_RECOIL = 14            # boss is pushed back this many pixels when firing
BEAM_TIME = BEAM_CHARGE + BEAM_FIRE
ORB_RADIUS = 22


class Beam:
    # y: height of the beam (the attack's lane). color: the boss's beam color.
    def __init__(self, y, color):
        self.y = y
        self.color = pygame.Color(color)
        self.timer = 0.0
        self.hit = False

    @property
    def done(self):
        return self.timer >= BEAM_TIME

    def update(self, dt):
        self.timer += dt
        if not self.hit and self.timer >= BEAM_CHARGE:
            self.hit = True
            return "impact"
        return None

    # The boss gets pushed back a little while the beam is firing.
    def recoil(self):
        since = self.timer - BEAM_CHARGE
        if since < 0:
            return 0
        return BEAM_RECOIL * (1 - ease_out(clamp01(since / BEAM_FIRE)))

    # origin_x: where the beam leaves the boss; bob: the boss's float offset.
    def draw(self, screen, origin_x, bob=0):
        y = self.y + bob
        if self.timer < BEAM_CHARGE:
            k = ease_out(self.timer / BEAM_CHARGE)
            draw_orb(screen, self.color, (origin_x, y), ORB_RADIUS * (0.6 + 0.6 * k))
            return
        k = clamp01((self.timer - BEAM_CHARGE) / BEAM_FIRE)
        # Full width at once, then thins out; a little flicker keeps it alive.
        width = BEAM_WIDTH * (1 - ease_in(k, 2)) + random.uniform(-3, 3)
        if width <= 1:
            return
        rect = pygame.Rect(0, 0, origin_x, max(2, round(width)))
        rect.centery = y
        glow = rect.inflate(0, round(width * 0.9))
        glow_surf = pygame.Surface(glow.size, pygame.SRCALPHA)
        glow_surf.fill((*self.color[:3], 90))
        screen.blit(glow_surf, glow)
        pygame.draw.rect(screen, self.color, rect)
        core = rect.inflate(0, -round(width * 0.55))
        if core.height > 0:
            pygame.draw.rect(screen, (255, 255, 255), core)
        draw_orb(screen, self.color, (origin_x, y), ORB_RADIUS * (1.2 - 0.6 * k))


# A glowing ball: soft outer glow, solid color, white center.
def draw_orb(screen, color, center, radius):
    radius = max(1, round(radius))
    color = pygame.Color(color)
    glow = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
    pygame.draw.circle(glow, (*color[:3], 70), (radius * 2, radius * 2), radius * 2)
    screen.blit(glow, glow.get_rect(center=(round(center[0]), round(center[1]))))
    pygame.draw.circle(screen, color, center, radius)
    pygame.draw.circle(screen, (255, 255, 255), center, max(1, radius // 2))


# --- Player dodge and hurt --------------------------------------------------
DODGE_RISE = 0.12           # jump up (fast, so the attack passes underneath)
DODGE_HANG = 0.32           # stay in the air while the attack goes by
DODGE_FALL = 0.20           # land back on the spot
DODGE_TIME = DODGE_RISE + DODGE_HANG + DODGE_FALL
DODGE_HEIGHT = 225          # high enough to clear the top attack lane
DODGE_BACK = 45             # also hop a little backwards
GHOSTS = 3                  # faded after-images trailing the jump
GHOST_GAP = 0.035           # seconds between after-images
HURT_TIME = 0.35            # shake + red flash after taking a hit
HURT_SHAKE = 10


class PlayerMotion:
    def __init__(self):
        self.dodge_timer = None     # None = standing
        self.hurt_timer = 0.0

    @property
    def dodging(self):
        return self.dodge_timer is not None

    # Start the dodge. Already in the air: stay up for the new attack too.
    def dodge(self):
        if self.dodge_timer is None:
            self.dodge_timer = 0.0
        else:
            self.dodge_timer = min(self.dodge_timer, DODGE_RISE)

    def hurt(self):
        self.hurt_timer = HURT_TIME

    def update(self, dt):
        self.hurt_timer = max(0.0, self.hurt_timer - dt)
        if self.dodge_timer is not None:
            self.dodge_timer += dt
            if self.dodge_timer >= DODGE_TIME:
                self.dodge_timer = None

    # Dodge position at time t, as (dx, dy).
    @staticmethod
    def dodge_offset(t):
        if t < DODGE_RISE:
            k = ease_out(t / DODGE_RISE)
        elif t < DODGE_RISE + DODGE_HANG:
            k = 1.0
        else:
            k = 1 - ease_in(clamp01((t - DODGE_RISE - DODGE_HANG) / DODGE_FALL), 2)
        return -DODGE_BACK * k, -DODGE_HEIGHT * k

    # Where the player is right now, as (dx, dy) from the resting spot.
    def offset(self):
        x, y = 0, 0
        if self.dodge_timer is not None:
            x, y = self.dodge_offset(self.dodge_timer)
        if self.hurt_timer > 0:
            x += random.uniform(-1, 1) * HURT_SHAKE * self.hurt_timer / HURT_TIME
        return round(x), round(y)

    # Offsets of the after-images, oldest first (only while dodging).
    def ghost_offsets(self):
        if self.dodge_timer is None:
            return []
        times = [self.dodge_timer - GHOST_GAP * i for i in range(GHOSTS, 0, -1)]
        return [tuple(map(round, self.dodge_offset(t))) for t in times if t > 0]

    # How strong the red hurt flash is, from 0 to 1.
    def hurt_flash(self):
        return self.hurt_timer / HURT_TIME
