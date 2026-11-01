import math
import pygame
from settings import HITBOX_WIDTH, HITBOX_HEIGHT, FONT_PATH
from systems.tilemap import touches_solid
from entities.player import AnimatedSprite


class Enemy:
    """วนสถานะ: patrol -> alert -> chase -> return -> patrol (ชนผู้เล่นตอน chase = เริ่มสู้)"""

    def __init__(self, x, y, idle_path, walk_paths, walk_dir, size=(64, 87),
                 patrol_range=150, speed=2, chase_speed=3,
                 detect_radius=200, lose_radius=400, alert_time=0.5, name="Enemy"):
        self.sprite = AnimatedSprite(idle_path, walk_paths, size=size, walk_dir=walk_dir)
        self.rect = pygame.Rect(x, y, *size)                          # กรอบรูป (ใช้วาด)
        self.hitbox = pygame.Rect(0, 0, HITBOX_WIDTH, HITBOX_HEIGHT)  # กรอบที่เท้า (ใช้ชน)
        self.hitbox.midbottom = self.rect.midbottom

        self.name = name
        self.spawn = (x, y)
        self.patrol_range = patrol_range
        self.speed = speed
        self.chase_speed = chase_speed        # ช้ากว่าผู้เล่น (4) จึงวิ่งหนีทัน
        self.detect_radius = detect_radius
        self.lose_radius = lose_radius        # ผู้เล่นหนีไกลเกินนี้ ศัตรูเลิกไล่
        self.alert_time = alert_time

        self.state = "patrol"
        self.direction = 1
        self.alert_timer = 0.0
        self.defeated = False
        self.stunned = 0.0                    # ช่วงที่ศัตรูไม่ตรวจจับผู้เล่น (ใช้หลังผู้เล่นหนีจากการสู้)

        # เรนเดอร์ข้อความไว้ล่วงหน้า ตอนวาดแค่แปะภาพ
        name_font = pygame.font.Font(FONT_PATH, 24)
        self.name_label = name_font.render(name, False, "#FFFFFF")
        self.name_shadow = name_font.render(name, False, "#000000")
        self.alert_mark = pygame.font.Font(None, 48).render("!", True, (255, 60, 60))

    def _move(self, dx, dy, solid):
        """ขยับทีละแกน ถ้าชนกำแพงให้ถอยกลับ คืน True ถ้าขยับได้จริง"""
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
        """เดินไปตามทิศ (tx, ty) ด้วยความเร็ว speed (ปรับทิศให้ยาว 1 ก่อน จะเดินเฉียงไม่เร็วขึ้น)"""
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
        """ใช้หลังผู้เล่นหนีจากการสู้: ศัตรูเดินกลับจุดเริ่มและไม่ตรวจจับผู้เล่นชั่วครู่"""
        self.state = "return"
        self.stunned = seconds

    def update(self, dt, player_rect, solid):
        """คืน True เมื่อศัตรูชนผู้เล่น (ถึงเวลาต่อสู้)"""
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
            self.sprite.facing_right = dx >= 0              # หันหน้าหาผู้เล่น
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

        else:  # return
            tx = self.spawn[0] - self.rect.x
            ty = self.spawn[1] - self.rect.y
            arrived = math.hypot(tx, ty) <= self.speed
            if arrived or not self._walk_toward(tx, ty, self.speed, solid):
                self._respawn()                             # ถึงแล้ว หรือติดกำแพง -> วางที่จุดเริ่ม
            elif self.stunned <= 0 and dist <= self.detect_radius:
                self._start_alert()                         # เห็นผู้เล่นระหว่างทางกลับ

        self.sprite.update(dt)
        return False

    def draw(self, screen, cam_x, cam_y):
        if self.defeated:
            return
        x = self.rect.x - cam_x                             # พิกัดโลก -> พิกัดจอ
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
        """คืนศัตรูที่ต้องสู้ด้วย (ถ้ามี) ไม่งั้นคืน None"""
        for enemy in self.enemies:
            if enemy.update(dt, player_rect, solid):
                return enemy
        return None

    def enemy_in_front(self, player_rect, facing_right, reach=20):
        """ใช้ตอนกดปุ่มท้าสู้: ขยายกรอบผู้เล่นไปด้านที่หันอยู่แล้วเช็กว่าชนศัตรูไหม"""
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