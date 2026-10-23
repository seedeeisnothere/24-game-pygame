import pygame
from settings import *
from systems.tilemap import *
from entities.player import *

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    screen_rect = screen.get_rect()
    clock = pygame.time.Clock()
    font = pygame.font.Font("assets/fonts/BoldPixels.ttf")

    running = True
    below, above = load_map("data/maps/map2layer.json")
    solid = load_collision("data/maps/map2layer.json")
    world_width = below.get_width()
    world_height = below.get_height()

    walk_paths = [f"Walk{i}.png" for i in range(12)]
    sprite = AnimatedSprite("assets/sprites/player/idle.png", walk_paths, frame_duration_ms=WALK_FRAME_MS)
    player_rect = sprite.idle_right.get_rect(center=screen_rect.center)
    player_x = player_rect.x
    player_y = player_rect.y
    player_width = player_rect.width
    player_height = player_rect.height
    hitbox = pygame.Rect(0, 0, HITBOX_WIDTH, HITBOX_HEIGHT)
    hitbox_offset_x = (player_width - HITBOX_WIDTH) // 2
    hitbox_offset_y = player_height - HITBOX_HEIGHT

    while running:

        dt = clock.tick(60) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        left  = keys[pygame.K_LEFT]  or keys[pygame.K_a]
        right = keys[pygame.K_RIGHT] or keys[pygame.K_d]
        up    = keys[pygame.K_UP]    or keys[pygame.K_w]
        down  = keys[pygame.K_DOWN]  or keys[pygame.K_s]

        if right and not left:
            sprite.facing_right = True
        elif left and not right:
            sprite.facing_right = False

        dx = right - left
        dy = down - up
        step = WALK_SPEED
        if dx != 0 and dy != 0:
            step = WALK_SPEED * 3 // 4

        old_x = player_x
        old_y = player_y

        player_x += dx * step
        player_x = max(0, min(player_x, world_width - player_width))
        hitbox.topleft = (player_x + hitbox_offset_x, player_y + hitbox_offset_y)
        if touches_solid(hitbox, solid):
            player_x = old_x

        player_y += dy * step
        player_y = max(0, min(player_y, world_height - player_height))
        hitbox.topleft = (player_x + hitbox_offset_x, player_y + hitbox_offset_y)
        if touches_solid(hitbox, solid):
            player_y = old_y

        sprite.moving = player_x != old_x or player_y != old_y
        sprite.update(dt)

        cam_x = player_x + player_width // 2 - SCREEN_WIDTH // 2
        cam_y = player_y + player_height // 2 - SCREEN_HEIGHT // 2

        cam_x = max(0, min(cam_x, world_width - SCREEN_WIDTH))
        cam_y = max(0, min(cam_y, world_height - SCREEN_HEIGHT))

        screen.fill((60, 90, 120))
        screen.blit(below, (-cam_x, -cam_y))
        screen.blit(sprite.get_image(), (player_x - cam_x, player_y - cam_y))
        screen.blit(above, (-cam_x, -cam_y))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()