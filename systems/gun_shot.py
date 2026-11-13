import math
import random
import pygame

GUN_HAND_PATH = "assets/item_assets/Gun_Hand.png"
GUN_WIDTH = 128                 # on-screen width of the gun hand
# The barrel in the PNG points slightly down; rotate by this to make it level.
BARREL_TILT = 6

# Timeline of one shot, in seconds from the start.
DRAW_TIME = 0.18                # gun swings up from the hip
FIRE_AT = 0.22                  # trigger is pulled
BULLET_TIME = 0.10              # bullet flies to the enemy
HOLSTER_AT = 0.70               # gun starts going back down
SHOT_TIME = 0.90                # everything is finished

HIP_ANGLE = -85                 # degrees: barrel pointing at the ground
RECOIL_ANGLE = 22               # barrel kicks up this much when firing
RECOIL_PUSH = 14                # gun slides back this many pixels
RECOIL_TIME = 0.18              # how long the kick takes to settle
FLASH_TIME = 0.06               # muzzle flash on screen
HIT_FLASH_TIME = 0.15           # enemy blinks white
SHAKE_TIME = 0.22               # enemy shakes after the hit
SHAKE_PIXELS = 8

# Where the muzzle is inside the gun image, as a fraction of its size.
MUZZLE = (0.97, 0.37)
# The hand (rotation pivot) inside the gun image.
GRIP = (0.25, 0.55)

FLASH_COLOR = (255, 230, 120)
FLASH_CORE = (255, 255, 230)
BULLET_COLOR = (255, 240, 180)


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def ease_in(t):
    t = max(0.0, min(1.0, t))
    return t * t


# Rotate (x, y) by angle degrees, using pygame's direction (counterclockwise).
def rotate_point(x, y, degrees):
    rad = math.radians(-degrees)
    return x * math.cos(rad) - y * math.sin(rad), x * math.sin(rad) + y * math.cos(rad)


# The player's quickdraw: the gun hand is pulled from the hip, fires one
# bullet at the enemy, then goes back to the hip.
class GunShot:
    # hip: where the hand rests (holster); aim: where the hand stops when aiming.
    # enemy_rect: the enemy on screen; the bullet flies straight into it.
    def __init__(self, hip, aim, enemy_rect):
        image = pygame.image.load(GUN_HAND_PATH).convert_alpha()
        height = round(image.get_height() * GUN_WIDTH / image.get_width())
        self.image = pygame.transform.smoothscale(image, (GUN_WIDTH, height))
        self.hip = pygame.Vector2(hip)
        self.aim = pygame.Vector2(aim)
        # Offsets from the grip (pivot) to the image center and to the muzzle.
        w, h = self.image.get_size()
        self.center_off = pygame.Vector2(w / 2 - GRIP[0] * w, h / 2 - GRIP[1] * h)
        self.muzzle_off = pygame.Vector2(MUZZLE[0] * w - GRIP[0] * w, MUZZLE[1] * h - GRIP[1] * h)
        # The gun aims level, so the bullet flies straight across at muzzle
        # height (kept inside the enemy so short enemies still get hit).
        self.aim_angle = 0
        muzzle_y = self.aim.y + rotate_point(*self.muzzle_off, BARREL_TILT)[1]
        rect = pygame.Rect(enemy_rect)
        target_y = max(rect.top + rect.height * 0.25, min(rect.bottom - rect.height * 0.15, muzzle_y))
        self.target = pygame.Vector2(rect.centerx, target_y)

        self.timer = None           # None = not shooting
        self.fired = False
        self.hit = False
        self.sparks = []

    @property
    def active(self):
        return self.timer is not None

    # Start a new shot (restarts if one is already playing).
    def start(self):
        self.timer = 0.0
        self.fired = False
        self.hit = False
        self.sparks = []

    # Advance the animation. Returns "fire" or "hit" on the frame it happens.
    def update(self, dt):
        if self.timer is None:
            return None
        self.timer += dt
        event = None
        if not self.fired and self.timer >= FIRE_AT:
            self.fired = True
            event = "fire"
        if not self.hit and self.timer >= FIRE_AT + BULLET_TIME:
            self.hit = True
            event = "hit"
            for _ in range(10):
                angle = random.uniform(0, math.tau)
                speed = random.uniform(150, 420)
                self.sparks.append([self.target.x, self.target.y,
                                    math.cos(angle) * speed, math.sin(angle) * speed, 0.3])
        for spark in self.sparks:
            spark[0] += spark[2] * dt
            spark[1] += spark[3] * dt
            spark[3] += 900 * dt        # gravity
            spark[4] -= dt
        self.sparks = [s for s in self.sparks if s[4] > 0]
        if self.timer >= SHOT_TIME:
            self.timer = None
        return event

    # Grip position and angle of the gun right now.
    def pose(self):
        t = self.timer
        if t < DRAW_TIME:
            k = ease_out(t / DRAW_TIME)
            # Swing in an arc: forward first, then up, like pulling from a holster.
            pos = self.hip.lerp(self.aim, k)
            pos.y += math.sin(k * math.pi) * 10
            return pos, HIP_ANGLE + (self.aim_angle - HIP_ANGLE) * k
        if t < HOLSTER_AT:
            pos = pygame.Vector2(self.aim)
            angle = self.aim_angle
            since_fire = t - FIRE_AT
            if since_fire >= 0:
                kick = 1 - ease_out(since_fire / RECOIL_TIME)
                angle += RECOIL_ANGLE * kick
                pos.x -= RECOIL_PUSH * kick
            return pos, angle
        k = ease_in((t - HOLSTER_AT) / (SHOT_TIME - HOLSTER_AT))
        return self.aim.lerp(self.hip, k), self.aim_angle + (HIP_ANGLE - self.aim_angle) * k

    # How far the enemy should be shaken right now, as (dx, dy).
    def enemy_shake(self):
        if self.timer is None or not self.hit:
            return 0, 0
        left = 1 - (self.timer - FIRE_AT - BULLET_TIME) / SHAKE_TIME
        if left <= 0:
            return 0, 0
        return (round(random.uniform(-1, 1) * SHAKE_PIXELS * left),
                round(random.uniform(-1, 1) * SHAKE_PIXELS * left * 0.5))

    # 0..1 strength of the white hit flash on the enemy.
    def enemy_flash(self):
        if self.timer is None or not self.hit:
            return 0.0
        return max(0.0, 1 - (self.timer - FIRE_AT - BULLET_TIME) / HIT_FLASH_TIME)

    def draw(self, screen):
        for x, y, _, _, life in self.sparks:
            size = max(1, round(5 * life / 0.3))
            pygame.draw.rect(screen, FLASH_COLOR, (round(x) - size // 2, round(y) - size // 2, size, size))
        if self.timer is None:
            return
        grip, angle = self.pose()
        # Fade in at the very start and out at the very end, so it "appears" at the hip.
        alpha = 255
        if self.timer < DRAW_TIME * 0.4:
            alpha = round(255 * self.timer / (DRAW_TIME * 0.4))
        elif self.timer > SHOT_TIME - 0.08:
            alpha = round(255 * max(0.0, (SHOT_TIME - self.timer) / 0.08))
        # angle is where the barrel points; the PNG needs a little extra turn.
        turn = angle + BARREL_TILT
        image = pygame.transform.rotate(self.image, turn)
        image.set_alpha(alpha)
        center = grip + pygame.Vector2(rotate_point(*self.center_off, turn))
        screen.blit(image, image.get_rect(center=(round(center.x), round(center.y))))

        muzzle = grip + pygame.Vector2(rotate_point(*self.muzzle_off, turn))
        since_fire = self.timer - FIRE_AT
        # Muzzle flash: a star of bright lines plus a hot core.
        if 0 <= since_fire < FLASH_TIME:
            k = 1 - since_fire / FLASH_TIME
            rad = math.radians(-angle)
            for spread, length in ((0, 46), (0.5, 24), (-0.5, 24), (1.2, 14), (-1.2, 14)):
                end = muzzle + pygame.Vector2(math.cos(rad + spread), math.sin(rad + spread)) * length * k
                pygame.draw.line(screen, FLASH_COLOR, muzzle, end, 6)
            pygame.draw.circle(screen, FLASH_CORE, muzzle, round(12 * k) + 2)
        # Bullet streak from the muzzle to the target.
        if 0 <= since_fire < BULLET_TIME:
            k = since_fire / BULLET_TIME
            head = pygame.Vector2(muzzle).lerp(self.target, k)
            tail = pygame.Vector2(muzzle).lerp(self.target, max(0.0, k - 0.25))
            pygame.draw.line(screen, BULLET_COLOR, tail, head, 4)
            pygame.draw.circle(screen, (255, 255, 255), head, 4)
