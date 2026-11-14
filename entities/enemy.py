import glob
import json
import os
import math
import random
import pygame
from settings import HITBOX_WIDTH, HITBOX_HEIGHT, FONT_PATH
from systems.tilemap import touches_solid

ENEMY_DATA_PATH = "data/enemies.json"

SLIME_SHEET_PATH = "assets/sprites/slime/slime.png"
SLIME_FRAME = 32                    # each cell on the sheet is 32 x 32
SLIME_COLORS = ("Blue", "Green", "Red")   # one sheet row per color
SLIME_FRAMES = 6                    # frames per row (one full hop)
# Every frame's slime fits inside this part of its cell, so we crop the
# empty space above it (keeps the name tag and hitbox right on the body).
SLIME_CROP = pygame.Rect(7, 18, 18, 14)


# Read one enemy's stats (name, hp, rewards, battle settings) from JSON.
def load_enemy_data(enemy_id, path=ENEMY_DATA_PATH):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)["enemies"][enemy_id]


# Slime animation cut from the sprite sheet. Works like the player's AnimatedSprite
# (same attributes/methods) so Enemy can use either one.
class SlimeSprite:
    # tint (optional RGB) multiplies the colors, e.g. to make darker cave slimes.
    def __init__(self, color=None, scale=4, battle_scale=10, frame_duration_ms=110, tint=None):
        sheet = pygame.image.load(SLIME_SHEET_PATH).convert_alpha()
        if color is None:
            color = random.choice(SLIME_COLORS)
        self.color = color
        row = SLIME_COLORS.index(color)

        frames = []
        for col in range(SLIME_FRAMES):
            crop = SLIME_CROP.move(col * SLIME_FRAME, row * SLIME_FRAME)
            frame = sheet.subsurface(crop).copy()
            if tint:
                frame.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
            frames.append(frame)
        size = (SLIME_CROP.width * scale, SLIME_CROP.height * scale)
        self.size = size

        # Whole-number scaling keeps the pixel art crisp
        self.walk_right = [pygame.transform.scale(f, size) for f in frames]
        self.walk_left = [pygame.transform.flip(f, True, False) for f in self.walk_right]
        self.idle_right = self.walk_right[0]
        self.idle_left = self.walk_left[0]
        # Big left-facing copy for the battle screen
        big = (SLIME_CROP.width * battle_scale, SLIME_CROP.height * battle_scale)
        self.battle_image = pygame.transform.flip(
            pygame.transform.scale(frames[0], big), True, False)

        self.frame_duration = frame_duration_ms / 1000
        self.frame_index = 0
        self.timer = 0.0
        self.moving = False
        self.facing_right = True

    # Advance the hop animation using the frame time dt.
    def update(self, dt):
        if not self.moving:
            self.frame_index = 0
            self.timer = 0.0
            return
        self.timer += dt
        if self.timer >= self.frame_duration:
            self.timer -= self.frame_duration
            self.frame_index = (self.frame_index + 1) % len(self.walk_right)

    def get_image(self):
        if self.moving:
            frames = self.walk_right if self.facing_right else self.walk_left
            return frames[self.frame_index]
        return self.idle_right if self.facing_right else self.idle_left


# Boss animation from a folder of numbered frames (frame_01.png, frame_02.png...).
# The monsters float, so the animation always loops, even when standing still.
# They face the camera, so there are no left/right versions.
class MonsterSprite:
    def __init__(self, folder, scale=2, battle_scale=5, frame_duration_ms=100):
        paths = sorted(glob.glob(os.path.join(folder, "frame_*.png")))
        if not paths:
            raise FileNotFoundError(f"no frame_*.png in {folder}")
        frames = [pygame.image.load(p).convert_alpha() for p in paths]
        w, h = frames[0].get_size()
        # Whole-number scaling keeps the pixel art crisp
        self.frames = [pygame.transform.scale(f, (w * scale, h * scale)) for f in frames]
        self.idle_right = self.idle_left = self.frames[0]
        self.battle_image = pygame.transform.scale(frames[0], (w * battle_scale, h * battle_scale))

        self.frame_duration = frame_duration_ms / 1000
        self.frame_index = 0
        self.timer = 0.0
        self.moving = False         # kept so Enemy can set it; not used
        self.facing_right = True

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.frame_duration:
            self.timer -= self.frame_duration
            self.frame_index = (self.frame_index + 1) % len(self.frames)

    def get_image(self):
        return self.frames[self.frame_index]


# An overworld enemy that patrols, notices the player, and chases them.
# States: "patrol" -> "alert" -> "chase" -> "return" (back to spawn).
class Enemy:
    # `sprite` is a SlimeSprite or MonsterSprite (anything with idle_right etc.).
    def __init__(self, x, y, sprite, patrol_range=150, speed=2, chase_speed=3,
                 detect_radius=200, lose_radius=400, alert_time=0.5,
                 name=None, enemy_id="enemy_1", kind=None):
        size = sprite.idle_right.get_size()
        self.sprite = sprite
        self.kind = kind            # e.g. "slime"; quests count kills by kind
        self.rect = pygame.Rect(x, y, *size)
        # Small hitbox at the feet, used for wall collision
        self.hitbox = pygame.Rect(0, 0, HITBOX_WIDTH, HITBOX_HEIGHT)
        self.hitbox.midbottom = self.rect.midbottom

        data = load_enemy_data(enemy_id)
        self.name = name or data["name"]
        self.hp = data["hp"]
        self.coin_reward = tuple(data["coin_reward"])
        self.battle = data["battle"]
        self.enemy_id = enemy_id
        # Optional story lines before the first fight / after winning it
        self.intro_dialogue = data.get("intro_dialogue")
        self.outro_dialogue = data.get("outro_dialogue")
        self.spawn = (x, y)
        self.patrol_range = patrol_range
        self.speed = speed
        self.chase_speed = chase_speed
        self.detect_radius = detect_radius
        self.lose_radius = lose_radius
        self.alert_time = alert_time

        self.state = "patrol"
        self.direction = 1          # 1 = right, -1 = left while patrolling
        self.alert_timer = 0.0
        self.defeated = False
        self.stunned = 0.0          # seconds left where it ignores the player

        # Pre-render the name tag and "!" so we don't render text every frame
        name_font = pygame.font.Font(FONT_PATH, 24)
        self.name_label = name_font.render(self.name, False, "#FFFFFF")
        self.name_shadow = name_font.render(self.name, False, "#000000")
        self.alert_mark = pygame.font.Font(None, 48).render("!", True, (255, 60, 60))

    # Move by (dx, dy), undoing each axis that hits a wall.
    # Returns True if the enemy actually moved.
    def _move(self, dx, dy, solid):
        moved = False
        # Try x and y separately so the enemy can slide along walls
        for step_x, step_y in ((dx, 0), (0, dy)):
            old = self.rect.topleft
            self.rect.move_ip(step_x, step_y)
            self.hitbox.midbottom = self.rect.midbottom
            if touches_solid(self.hitbox, solid):
                self.rect.topleft = old
                self.hitbox.midbottom = self.rect.midbottom
            elif step_x or step_y:
                moved = True
        return moved

    # Step toward the offset (tx, ty) at the given speed.
    def _walk_toward(self, tx, ty, speed, solid):
        length = math.hypot(tx, ty)
        if length == 0:
            return False
        if tx:
            self.sprite.facing_right = tx > 0
        # Normalize the direction so speed is the same in every direction
        return self._move(round(tx / length * speed), round(ty / length * speed), solid)

    # Switch to the "alert" state and restart its timer.
    def _start_alert(self):
        self.state = "alert"
        self.alert_timer = 0.0

    # Snap back to the spawn point and start patrolling again.
    def _respawn(self):
        self.rect.topleft = self.spawn
        self.hitbox.midbottom = self.rect.midbottom
        self.state = "patrol"

    # Make the enemy walk home and ignore the player for a while.
    def stun(self, seconds=2.0):
        self.state = "return"
        self.stunned = seconds

    # Run the state machine for one frame.
    # Returns True when the enemy touches the player (start a battle).
    def update(self, dt, player_rect, solid):
        if self.defeated:
            return False
        self.stunned = max(0.0, self.stunned - dt)

        dx = player_rect.centerx - self.hitbox.centerx
        dy = player_rect.centery - self.hitbox.centery
        dist = math.hypot(dx, dy)
        self.sprite.moving = self.state != "alert"

        if self.state == "patrol":
            # Walk left and right; turn around at a wall or the patrol edge
            self.sprite.facing_right = self.direction > 0
            blocked = not self._move(self.direction * self.speed, 0, solid)
            if blocked or abs(self.rect.x - self.spawn[0]) >= self.patrol_range:
                self.direction *= -1
            if self.stunned <= 0 and dist <= self.detect_radius:
                self._start_alert()

        elif self.state == "alert":
            # Stand still and face the player briefly before chasing
            self.sprite.facing_right = dx >= 0
            self.alert_timer += dt
            if dist > self.lose_radius:
                self.state = "return"
            elif self.alert_timer >= self.alert_time:
                self.state = "chase"

        elif self.state == "chase":
            self._walk_toward(dx, dy, self.chase_speed, solid)
            if self.hitbox.colliderect(player_rect):
                return True
            if dist > self.lose_radius:
                self.state = "return"

        else:
            # "return": walk back to spawn; teleport if stuck or close enough
            tx = self.spawn[0] - self.rect.x
            ty = self.spawn[1] - self.rect.y
            arrived = math.hypot(tx, ty) <= self.speed
            if arrived or not self._walk_toward(tx, ty, self.speed, solid):
                self._respawn()
            elif self.stunned <= 0 and dist <= self.detect_radius:
                self._start_alert()

        self.sprite.update(dt)
        return False

    # Draw the enemy, its name tag, and a "!" when alerted.
    def draw(self, screen, cam_x, cam_y):
        if self.defeated:
            return
        # World position -> screen position
        x = self.rect.x - cam_x
        y = self.rect.y - cam_y
        screen.blit(self.sprite.get_image(), (x, y))

        center_x = x + self.rect.width // 2
        name_x = center_x - self.name_label.get_width() // 2
        name_y = y - self.name_label.get_height() - 4
        # Shadow first, offset by 2px, so the name is readable
        screen.blit(self.name_shadow, (name_x + 2, name_y + 2))
        screen.blit(self.name_label, (name_x, name_y))
        if self.state == "alert":
            screen.blit(self.alert_mark,
                        (center_x - self.alert_mark.get_width() // 2,
                         name_y - self.alert_mark.get_height()))


# Holds all enemies on the map and updates/draws them together.
class EnemyEncounter:
    def __init__(self, enemies):
        self.enemies = enemies

    # Return the first enemy that caught the player, or None.
    def update(self, dt, player_rect, solid):
        for enemy in self.enemies:
            if enemy.update(dt, player_rect, solid):
                return enemy
        return None

    # Return an enemy just in front of the player, or None.
    def enemy_in_front(self, player_rect, facing_right, reach=20):
        # Stretch the player's rect forward by `reach` pixels
        probe = player_rect.copy()
        probe.width += reach
        if not facing_right:
            probe.x -= reach
        for enemy in self.enemies:
            if not enemy.defeated and probe.colliderect(enemy.hitbox):
                return enemy
        return None

    # Keep the animations going while the enemies are frozen (dialogue, shop).
    def animate(self, dt):
        for enemy in self.enemies:
            if not enemy.defeated:
                enemy.sprite.update(dt)

    def draw(self, screen, cam_x, cam_y):
        for enemy in self.enemies:
            enemy.draw(screen, cam_x, cam_y)


# Spawns 1-2 enemies in a zone. After they're all beaten and the
# player walks far away, a new wave appears (for farming coins).
class EnemySpawner:
    def __init__(self, zone, make_enemy, solid, wave_size=(1, 2),
                 respawn_distance=900, rng=None):
        self.zone = zone
        self.make_enemy = make_enemy    # function (x, y) -> Enemy
        self.solid = solid
        self.wave_size = wave_size
        self.respawn_distance = respawn_distance
        self.rng = rng or random.Random()
        self.wave = []

    # True when every enemy in the current wave is defeated.
    @property
    def cleared(self):
        return all(enemy.defeated for enemy in self.wave)

    # True when the point is far enough from the zone center.
    def far_from(self, point):
        return math.dist(point, self.zone.center) >= self.respawn_distance

    # Place a new wave at random free spots inside the zone.
    def spawn_wave(self):
        self.wave = []
        count = self.rng.randint(*self.wave_size)
        # Try up to 30 random spots per enemy to find free places
        for _ in range(count * 30):
            if len(self.wave) == count:
                break
            # Make the enemy first so we know its size, then keep it inside the zone
            enemy = self.make_enemy(self.zone.left, self.zone.top)
            w, h = enemy.rect.size
            x = self.rng.randint(self.zone.left, self.zone.right - w)
            y = self.rng.randint(self.zone.top, self.zone.bottom - h)
            enemy.rect.topleft = (x, y)
            enemy.spawn = (x, y)
            enemy.hitbox.midbottom = enemy.rect.midbottom
            if touches_solid(enemy.hitbox, self.solid):
                continue
            # Skip spots too close to an enemy already in this wave
            if any(abs(other.rect.x - x) < 160 and abs(other.rect.y - y) < 120
                   for other in self.wave):
                continue
            self.wave.append(enemy)
        return self.wave

    # Return the new enemies if a wave just spawned, otherwise [].
    def update(self, player_center):
        if self.wave and not self.cleared:
            return []
        if self.wave and not self.far_from(player_center):
            return []
        return self.spawn_wave()
