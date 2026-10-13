import pygame  # type: ignore[import-not-found]
from settings import *

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    screen_rect = screen.get_rect()
    clock = pygame.time.Clock()
    font = pygame.font.Font("assets/fonts/BoldPixels.ttf")

    running = True
    map_x, map_y = 0, 0
    background_map = pygame.image.load("placeholder_map.png").convert()
    map_rect_topleft = background_map.get_rect(topleft=(0, 0))
    map_rect_bottomright = background_map.get_rect(bottomright=(1280, 800))

    car = pygame.image.load("assets/sprites/car.png").convert_alpha()
    car = pygame.transform.scale(car, (96, 96))
    car_rect = car.get_rect(center=screen_rect.center)
    car_x = tuple(car_rect)[0]
    car_y = tuple(car_rect)[1]

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            if car_x > tuple(car_rect)[0]:
                car_x -= 5
            else:
                if map_x < tuple(map_rect_topleft)[0]:
                    map_x += 5
                else:
                    car_x -= 5
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            if car_x < tuple(car_rect)[0]:
                car_x += 5
            else:
                if map_x > tuple(map_rect_bottomright)[0]:
                    map_x -= 5
                else:
                    car_x += 5
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            if car_y > tuple(car_rect)[1]:
                car_y -= 5
            else:
                if map_y < tuple(map_rect_topleft)[1]:
                    map_y += 5
                else:
                    car_y -= 5
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            if car_y < tuple(car_rect)[1]:
                car_y += 5
            else:
                if map_y > tuple(map_rect_bottomright)[1]:
                    map_y -= 5
                else:
                    car_y += 5


        screen.blit(background_map, (map_x, map_y))
        screen.blit(car, (car_x, car_y))

        pygame.display.update()

        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()