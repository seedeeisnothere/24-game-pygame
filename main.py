import pygame

SCREEN_HEIGHT = 600
SCREEN_WIDTH = 960
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
running = True


while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill("black")

    pygame.display.update()

    clock.tick(60)

pygame.quit()