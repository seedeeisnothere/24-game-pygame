import os
import pygame
from settings import MUSIC_PATHS, MUSIC_GAIN, MUSIC_FADE_MS, MUSIC_MASTER


# Plays one background track at a time, with a short fade between tracks.
class MusicPlayer:
    def __init__(self, volume):
        self.current = None
        self.volume = volume
        self.apply_volume()

    # volume is the BGM slider value; each track also has its own gain
    # (MUSIC_GAIN) so all songs sound equally loud.
    def set_volume(self, volume):
        self.volume = volume
        self.apply_volume()

    def apply_volume(self):
        gain = MUSIC_GAIN.get(self.current, 1.0)
        pygame.mixer.music.set_volume(self.volume * gain * MUSIC_MASTER)

    # Start a track by name (see MUSIC_PATHS). Does nothing if it's already on,
    # so walking back into a scene doesn't restart its song.
    def play(self, name, loop=True):
        if name == self.current:
            return
        self.current = name
        if name is None:
            pygame.mixer.music.fadeout(MUSIC_FADE_MS)
            return
        path = MUSIC_PATHS[name]
        # Missing file: keep the game running in silence.
        if not os.path.exists(path):
            print(f"[music] missing {path}, skipping")
            pygame.mixer.music.fadeout(MUSIC_FADE_MS)
            return
        pygame.mixer.music.load(path)
        self.apply_volume()
        pygame.mixer.music.play(-1 if loop else 0, fade_ms=MUSIC_FADE_MS)
