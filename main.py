import pygame
from pyvidplayer2 import Video

SCREEN_HEIGHT = 800
SCREEN_WIDTH = 1280
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
font = pygame.font.Font("24game/assets/fonts/cmu.serif-roman.ttf", 80)
intro_vid = Video("/Users/seedee/Documents/Python Workspace/24game/assets/video/intro.mp4", interp="area")
intro_vid.resize((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    intro_vid.draw(screen, (0, 0))
    pygame.display.flip()

pygame.quit()