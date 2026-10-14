import pygame
from settings import *
from systems.tilemap import *

def main():
    global screen
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    screen_rect = screen.get_rect()
    clock = pygame.time.Clock()
    font = pygame.font.Font("assets/fonts/BoldPixels.ttf")

    running = True
    map_x, map_y = 0, 0
    tiles = load_tiles("assets/tiles/Grass.png")
    map_surface = load_map("assets/map/map.json", tiles)
    map_rect_topleft = map_surface.get_rect(topleft=(0, 0))
    map_rect_bottomright = map_surface.get_rect(bottomright=(1280, 800))

    car = pygame.image.load("assets/sprites/car.png").convert_alpha()
    car = pygame.transform.scale(car, (96, 60))
    car_rect = car.get_rect(center=screen_rect.center)
    car_x = tuple(car_rect)[0]
    car_y = tuple(car_rect)[1]

    move_speed = 4

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            if car_x > tuple(car_rect)[0]:
                car_x -= move_speed
            else:
                if map_x < tuple(map_rect_topleft)[0]:
                    map_x += move_speed
                else:
                    if car_x > 0:
                        car_x -= move_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            if car_x < tuple(car_rect)[0]:
                car_x += move_speed
            else:
                if map_x > tuple(map_rect_bottomright)[0]:
                    map_x -= move_speed
                else:
                    if car_x < tuple(car.get_rect(bottomright=(1280, 800)))[0]:
                        car_x += move_speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            if car_y > tuple(car_rect)[1]:
                car_y -= move_speed
            else:
                if map_y < tuple(map_rect_topleft)[1]:
                    map_y += move_speed
                else:
                    if car_y > 0:
                        car_y -= move_speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            if car_y < tuple(car_rect)[1]:
                car_y += move_speed
            else:
                if map_y > tuple(map_rect_bottomright)[1]:
                    map_y -= move_speed
                else:
                    if car_y < tuple(car.get_rect(bottomright=(1280, 800)))[1]:
                        car_y += move_speed


        screen.fill((60, 90, 120))
        screen.blit(map_surface, (map_x, map_y))
        screen.blit(car, (car_x, car_y))

        
        pygame.display.flip()

        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()