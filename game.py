import pygame
import random
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
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SCALED, vsync=1)
        self.screen_rect = self.screen.get_rect()
        self.clock = pygame.time.Clock()
        self.running = True
        self.sfx_volume = DEFAULT_SFX_VOLUME
        self.bgm_volume = DEFAULT_BGM_VOLUME
        self.sounds = {
            "hover": pygame.mixer.Sound(HOVER_SFX_PATH),
            "select": pygame.mixer.Sound(SELECT_SFX_PATH),
        }
        self.walk_grass_sounds = [pygame.mixer.Sound(path) for path in WALK_GRASS_SFX_PATHS]
        self.next_walk_sfx_time = 0
        self.scene = None
        self.next_scene = None
        self.curtain = Curtain()
        self.set_scene("title")

    def set_scene(self, name):
        self.scene = SCENES[name](self)

    def play_sfx(self, name):
        sound = self.sounds[name]
        sound.set_volume(self.sfx_volume)
        sound.play()

    def update_walk_sfx(self, moving):
        now = pygame.time.get_ticks()
        if moving and now >= self.next_walk_sfx_time:
            sound = random.choice(self.walk_grass_sounds)
            sound.set_volume(self.sfx_volume * WALK_GRASS_VOLUME)
            sound.play()
            self.next_walk_sfx_time = now + round(sound.get_length() * 1000) + WALK_GRASS_DELAY_MS

    def change_scene(self, target):
        if self.curtain.is_busy():
            return
        self.next_scene = target
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
            if self.curtain.state in ("idle", "holding", "opening"):
                self.scene.update(dt)                 # ตอนม่านกำลังปิด ไม่อัปเดต = ภาพค้าง
            self.curtain.update(dt)
            self.scene.draw(self.screen)
            self.curtain.draw(self.screen)
            pygame.display.flip()
            if self.curtain.state == "covered":
                target = self.next_scene
                self.scene = SCENES[target](self) if isinstance(target, str) else target()
                self.curtain.finish_loading()
        pygame.quit()


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()

    print('k')