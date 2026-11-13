import pygame
import random
from settings import *
from systems.transition import Curtain
from scenes.title_scene import TitleScene
from scenes.overworld_scene import OverworldScene
from systems.game_state import GameState
from scenes.gameover_scene import GameOverScene
from systems.audio import MusicPlayer

# Scene names mapped to their classes
SCENES = {
    "title": TitleScene,
    "overworld": OverworldScene,
    "gameover": GameOverScene,
}


# Owns the window, sounds, shared game state, and the current scene.
class Game:
    def __init__(self):
        pygame.init()
        # SCALED stretches the window but keeps the game's own resolution
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT),
                                              pygame.SCALED, vsync=1)
        self.screen_rect = self.screen.get_rect()
        self.clock = pygame.time.Clock()
        self.running = True
        self.sfx_volume = DEFAULT_SFX_VOLUME
        self.bgm_volume = DEFAULT_BGM_VOLUME
        self.music = MusicPlayer(self.bgm_volume)
        self.sounds = {
            "hover": pygame.mixer.Sound(HOVER_SFX_PATH),
            "select": pygame.mixer.Sound(SELECT_SFX_PATH),
            "pickup": pygame.mixer.Sound(PICKUP_SFX_PATH),
            "explosion": pygame.mixer.Sound(EXPLOSION_SFX_PATH),
            "shoot": pygame.mixer.Sound(SHOOT_SFX_PATH),
            "hit": pygame.mixer.Sound(HIT_SFX_PATH),
            "death": pygame.mixer.Sound(DEATH_SFX_PATH),
            "powerup": pygame.mixer.Sound(POWERUP_SFX_PATH),
        }
        self.walk_grass_sounds = [pygame.mixer.Sound(path) for path in WALK_GRASS_SFX_PATHS]
        self.next_walk_sfx_time = 0
        self.scene = None
        self.next_scene = None
        self.curtain = Curtain()
        self.state = GameState()
        self.overworlds = {}
        self.set_scene("title")

    # Switch scene right away, with no curtain.
    def set_scene(self, name):
        self.scene = SCENES[name](self)
        self.play_scene_music()

    # Each scene names its track in .music (None = keep whatever is playing).
    def play_scene_music(self):
        name = getattr(self.scene, "music", None)
        if name is not None:
            self.music.play(name, getattr(self.scene, "music_loop", True))

    # Play a short sound effect at the current SFX volume.
    def play_sfx(self, name):
        sound = self.sounds[name]
        sound.set_volume(self.sfx_volume)
        sound.play()

    # Play a random footstep sound while walking, one at a time.
    def update_walk_sfx(self, moving):
        now = pygame.time.get_ticks()
        if moving and now >= self.next_walk_sfx_time:
            sound = random.choice(self.walk_grass_sounds)
            sound.set_volume(self.sfx_volume * WALK_GRASS_VOLUME)
            sound.play()
            # Next step can play after this sound ends plus a short delay
            self.next_walk_sfx_time = (now + round(sound.get_length() * 1000)
                                       + WALK_GRASS_DELAY_MS)

    # Start a curtain transition to a new scene.
    # target is a scene name or a function that builds a scene.
    def change_scene(self, target):
        if self.curtain.is_busy():
            return
        self.next_scene = target
        self.curtain.start()

    # The main game loop: input -> update -> draw, once per frame.
    def run(self):
        while self.running:
            # dt = seconds since last frame, capped so lag spikes don't jump
            dt = min(self.clock.tick(FPS) / 1000, MAX_DT)
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    self.running = False
            # Ignore input while the curtain is moving
            if not self.curtain.is_busy():
                self.scene.handle_events(events)
            # Freeze the scene while the curtain is closing or fully closed
            if self.curtain.state in ("idle", "holding", "opening"):
                self.scene.update(dt)
            self.curtain.update(dt)
            self.scene.draw(self.screen)
            self.curtain.draw(self.screen)
            pygame.display.flip()
            # Screen is fully covered: swap to the next scene behind it
            if self.curtain.state == "covered":
                target = self.next_scene
                self.scene = SCENES[target](self) if isinstance(target, str) else target()
                self.play_scene_music()
                self.curtain.finish_loading()
        pygame.quit()


# Create the game and start the loop.
def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()