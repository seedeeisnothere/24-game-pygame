import pygame
from settings import *
from scenes.overworld_scene import OverworldScene


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.screen_rect = self.screen.get_rect()
        self.clock = pygame.time.Clock()
        self.running = True
        self.scene = OverworldScene(self)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
            self.scene.handle_events(events)
            self.scene.update(dt)
            self.scene.draw(self.screen)
            pygame.display.flip()
        pygame.quit()


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()