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
    map_x, map_y = 0, 0
    below, above = load_map("data/maps/map.json")
    map_rect_topleft = below.get_rect(topleft=(0, 0))
    map_rect_bottomright = below.get_rect(bottomright=(SCREEN_WIDTH, SCREEN_HEIGHT))

    walk_paths = [f"Walk{i}.png" for i in range(12)]
    sprite = AnimatedSprite("assets/sprites/player/idle.png", walk_paths, frame_duration_ms=75)
    player_rect = sprite.idle_right.get_rect(center=screen_rect.center)
    player_rect_bottomright = sprite.idle_right.get_rect(bottomright=(SCREEN_WIDTH, SCREEN_HEIGHT))
    player_x = player_rect.x
    player_y = player_rect.y

    move_speed = 4

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

        sprite.moving = left or right or up or down
        if right and not left:
            sprite.facing_right = True
        elif left and not right:
            sprite.facing_right = False

        sprite.update(dt)
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            if keys[pygame.K_LSHIFT]:
                sprite.frame_duration = 45 / 1000
                move_speed = 8
            else:
                sprite.frame_duration = 75 / 1000
                move_speed = 4
            if player_x > player_rect.x:
                player_x -= move_speed
            else:
                if map_x < map_rect_topleft.x:
                    map_x += move_speed
                else:
                    if player_x > 0:
                        player_x -= move_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            if keys[pygame.K_LSHIFT]:
                move_speed = 8
                sprite.frame_duration = 45 / 1000
            else:
                move_speed = 4
                sprite.frame_duration = 75 / 1000
            if player_x < player_rect.x:
                player_x += move_speed
            else:
                if map_x > map_rect_bottomright.x:
                    map_x -= move_speed
                else:
                    if player_x < player_rect_bottomright.x:
                        player_x += move_speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            if keys[pygame.K_LSHIFT]:
                move_speed = 8
                sprite.frame_duration = 45 / 1000
            else:
                move_speed = 4
                sprite.frame_duration = 75 / 1000
            if player_y > player_rect.y:
                player_y -= move_speed
            else:
                if map_y < map_rect_topleft.y:
                    map_y += move_speed
                else:
                    if player_y > 0:
                        player_y -= move_speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            if keys[pygame.K_LSHIFT]:
                move_speed = 8
                sprite.frame_duration = 45 / 1000
            else:
                move_speed = 4
                sprite.frame_duration = 75 / 1000
            if player_y < player_rect.y:
                player_y += move_speed
            else:
                if map_y > map_rect_bottomright.y:
                    map_y -= move_speed
                else:
                    if player_y < player_rect_bottomright.y:
                        player_y += move_speed


        screen.fill((60, 90, 120))
        screen.blit(below, (map_x, map_y))
        screen.blit(sprite.get_image(), (player_x, player_y))
        screen.blit(above, (map_x, map_y))

        
        pygame.display.flip()

        

    pygame.quit()

if __name__ == "__main__":
    main()