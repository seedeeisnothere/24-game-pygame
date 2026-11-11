import json
import math
import pygame
from settings import HITBOX_WIDTH, HITBOX_HEIGHT, FONT_PATH
from systems.tilemap import touches_solid
from entities.player import AnimatedSprite

ENEMY_DATA_PATH = "data/enemies.json"


def load_enemy_data(enemy_id, path=ENEMY_DATA_PATH):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)["enemies"][enemy_id]


class Enemy:
    def __init__(self, x, y, idle_path, walk_paths, walk_dir, size=(64, 87),
                 patrol_range=150, speed=2, chase_speed=3,
                 detect_radius=200, lose_radius=400, alert_time=0.5, name=None, enemy_id="enemy_1"):
        self.sprite = AnimatedSprite(idle_path, walk_paths, size=size, walk_dir=walk_dir)
        self.rect = pygame.Rect(x, y, *size)
        self.hitbox = pygame.Rect(0, 0, HITBOX_WIDTH, HITBOX_HEIGHT)
        self.hitbox.midbottom = self.rect.midbottom

        data = load_enemy_data(enemy_id)
        self.name = name or data["name"]
        self.hp = data["hp"]
        self.coin_reward = tuple(data["coin_reward"])
        self.battle = data["battle"]
        self.spawn = (x, y)
        self.patrol_range = patrol_range
        self.speed = speed
        self.chase_speed = chase_speed
        self.detect_radius = detect_radius
        self.lose_radius = lose_radius
        self.alert_time = alert_time

        self.state = "patrol"
        self.direction = 1
        self.alert_timer = 0.0
        self.defeated = False
        self.stunned = 0.0

        name_font = pygame.font.Font(FONT_PATH, 24)
        self.name_label = name_font.render(self.name, False, "#FFFFFF")
        self.name_shadow = name_font.render(self.name, False, "#000000")
        self.alert_mark = pygame.font.Font(None, 48).render("!", True, (255, 60, 60))

    def _move(self, dx, dy, solid):
        moved = False
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

    def _walk_toward(self, tx, ty, speed, solid):
        length = math.hypot(tx, ty)
        if length == 0:
            return False
        if tx:
            self.sprite.facing_right = tx > 0
        return self._move(round(tx / length * speed), round(ty / length * speed), solid)

    def _start_alert(self):
        self.state = "alert"
        self.alert_timer = 0.0

    def _respawn(self):
        self.rect.topleft = self.spawn
        self.hitbox.midbottom = self.rect.midbottom
        self.state = "patrol"

    def stun(self, seconds=2.0):
        self.state = "return"
        self.stunned = seconds

    def update(self, dt, player_rect, solid):
        if self.defeated:
            return False
        self.stunned = max(0.0, self.stunned - dt)

        dx = player_rect.centerx - self.hitbox.centerx
        dy = player_rect.centery - self.hitbox.centery
        dist = math.hypot(dx, dy)
        self.sprite.moving = self.state != "alert"

        if self.state == "patrol":
            self.sprite.facing_right = self.direction > 0
            blocked = not self._move(self.direction * self.speed, 0, solid)
            if blocked or abs(self.rect.x - self.spawn[0]) >= self.patrol_range:
                self.direction *= -1
            if self.stunned <= 0 and dist <= self.detect_radius:
                self._start_alert()

        elif self.state == "alert":
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
            tx = self.spawn[0] - self.rect.x
            ty = self.spawn[1] - self.rect.y
            arrived = math.hypot(tx, ty) <= self.speed
            if arrived or not self._walk_toward(tx, ty, self.speed, solid):
                self._respawn()
            elif self.stunned <= 0 and dist <= self.detect_radius:
                self._start_alert()

        self.sprite.update(dt)
        return False

    def draw(self, screen, cam_x, cam_y):
        if self.defeated:
            return
        x = self.rect.x - cam_x
        y = self.rect.y - cam_y
        screen.blit(self.sprite.get_image(), (x, y))

        center_x = x + self.rect.width // 2
        name_x = center_x - self.name_label.get_width() // 2
        name_y = y - self.name_label.get_height() - 4
        screen.blit(self.name_shadow, (name_x + 2, name_y + 2))
        screen.blit(self.name_label, (name_x, name_y))
        if self.state == "alert":
            screen.blit(self.alert_mark,
                        (center_x - self.alert_mark.get_width() // 2,
                         name_y - self.alert_mark.get_height()))


class EnemyEncounter:
    def __init__(self, enemies):
        self.enemies = enemies

    def update(self, dt, player_rect, solid):
        for enemy in self.enemies:
            if enemy.update(dt, player_rect, solid):
                return enemy
        return None

    def enemy_in_front(self, player_rect, facing_right, reach=20):
        probe = player_rect.copy()
        probe.width += reach
        if not facing_right:
            probe.x -= reach
        for enemy in self.enemies:
            if not enemy.defeated and probe.colliderect(enemy.hitbox):
                return enemy
        return None

    def draw(self, screen, cam_x, cam_y):
        for enemy in self.enemies:
            enemy.draw(screen, cam_x, cam_y)