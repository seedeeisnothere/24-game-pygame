import pygame
from settings import *
from systems.tilemap import *
from entities.player import *
from scenes.scene import Scene


class OverworldScene(Scene):
    def __init__(self, game):
        super().__init__(game)
        self.below, self.above = load_map(MAP_PATH)
        self.solid = load_collision(MAP_PATH)
        self.world_width = self.below.get_width()
        self.world_height = self.below.get_height()

        walk_paths = [f"Walk{i}.png" for i in range(12)]
        self.sprite = AnimatedSprite("assets/sprites/player/idle.png", walk_paths, frame_duration_ms=WALK_FRAME_MS)
        player_rect = self.sprite.idle_right.get_rect(center=self.game.screen_rect.center)
        self.player_x = player_rect.x
        self.player_y = player_rect.y
        self.player_width = player_rect.width
        self.player_height = player_rect.height
        self.hitbox = pygame.Rect(0, 0, HITBOX_WIDTH, HITBOX_HEIGHT)
        self.hitbox_offset_x = (self.player_width - HITBOX_WIDTH) // 2
        self.hitbox_offset_y = self.player_height - HITBOX_HEIGHT
        self.cam_x = 0
        self.cam_y = 0

    def update(self, dt):
        keys = pygame.key.get_pressed()
        left  = keys[pygame.K_LEFT]  or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        up    = keys[pygame.K_UP]    or keys[pygame.K_w]
        down  = keys[pygame.K_DOWN]  or keys[pygame.K_s]

        if right and not left:
            self.sprite.facing_right = True
        elif left and not right:
            self.sprite.facing_right = False

        dx = right - left
        dy = down - up
        step = WALK_SPEED
        if dx != 0 and dy != 0:
            step = WALK_SPEED * 3 // 4

        old_x = self.player_x
        old_y = self.player_y

        self.player_x += dx * step
        self.player_x = max(0, min(self.player_x, self.world_width - self.player_width))
        self.hitbox.topleft = (self.player_x + self.hitbox_offset_x, self.player_y + self.hitbox_offset_y)
        if touches_solid(self.hitbox, self.solid):
            self.player_x = old_x

        self.player_y += dy * step
        self.player_y = max(0, min(self.player_y, self.world_height - self.player_height))
        self.hitbox.topleft = (self.player_x + self.hitbox_offset_x, self.player_y + self.hitbox_offset_y)
        if touches_solid(self.hitbox, self.solid):
            self.player_y = old_y

        self.sprite.moving = self.player_x != old_x or self.player_y != old_y
        self.sprite.update(dt)

        self.cam_x = self.player_x + self.player_width // 2 - SCREEN_WIDTH // 2
        self.cam_y = self.player_y + self.player_height // 2 - SCREEN_HEIGHT // 2
        self.cam_x = max(0, min(self.cam_x, self.world_width - SCREEN_WIDTH))
        self.cam_y = max(0, min(self.cam_y, self.world_height - SCREEN_HEIGHT))

    def draw(self, screen):
        screen.fill((60, 90, 120))
        screen.blit(self.below, (-self.cam_x, -self.cam_y))
        screen.blit(self.sprite.get_image(), (self.player_x - self.cam_x, self.player_y - self.cam_y))
        screen.blit(self.above, (-self.cam_x, -self.cam_y))