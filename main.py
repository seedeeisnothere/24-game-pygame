import pygame  # type: ignore[import-not-found]

SCREEN_HEIGHT = 800
SCREEN_WIDTH = 1280
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    pygame.display.flip()

    clock.tick(60)

pygame.quit()