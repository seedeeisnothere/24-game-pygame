import pygame
from settings import *
from systems.transition import Curtain
from scenes.title_scene import TitleScene
from scenes.overworld_scene import OverworldScene


SCENES = {
    "title": TitleScene,
    "overworld": OverworldScene,
}


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.screen_rect = self.screen.get_rect()
        self.clock = pygame.time.Clock()
        self.running = True
        self.sfx_volume = DEFAULT_SFX_VOLUME
        self.bgm_volume = DEFAULT_BGM_VOLUME
        self.scene = None
        self.next_scene_name = None
        self.curtain = Curtain()
        self.set_scene("title")

    def set_scene(self, name):
        self.scene = SCENES[name](self)

    def change_scene(self, name):
        if self.curtain.is_busy():
            return
        self.next_scene_name = name
        self.curtain.start()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000, MAX_DT)
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
            if not self.curtain.is_busy():
                self.scene.handle_events(events)
            self.scene.update(dt)
            self.curtain.update(dt)
            self.scene.draw(self.screen)
            self.curtain.draw(self.screen)
            pygame.display.flip()
            if self.curtain.state == "covered":
                self.set_scene(self.next_scene_name)
                self.curtain.finish_loading()
        pygame.quit()


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()