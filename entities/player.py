import pygame

class AnimatedSprite:
    def __init__(self, idle_path, walk_paths, frame_duration_ms=75):
        # Load once, with transparency and fast drawing
        self.idle_right = pygame.transform.scale(pygame.image.load(idle_path).convert_alpha(), (64, 87))
        self.walk_right = [pygame.transform.scale(pygame.image.load(f"assets/sprites/player/walk/{p}").convert_alpha(), (64, 87)) for p in walk_paths]

        # Mirrored copies, built once so we never flip during the game loop
        self.idle_left = pygame.transform.flip(self.idle_right, True, False)
        self.walk_left = [pygame.transform.flip(f, True, False) for f in self.walk_right]

        self.frame_duration_ms = frame_duration_ms
        self.frame_index = 0
        self.timer = 0.0
        self.frame_duration = self.frame_duration_ms / 1000   # ms -> seconds, to match dt
        self.moving = False
        self.facing_right = True

    def update(self, dt):
        if not self.moving:
            self.frame_index = 0     # next walk starts at the first frame
            self.timer = 0.0         # and with a fresh timer
            return

        self.timer += dt
        if self.timer >= self.frame_duration:
            self.timer -= self.frame_duration                 # keep the leftover time
            self.frame_index = (self.frame_index + 1) % len(self.walk_right)

    def get_image(self):
        if self.moving:
            frames = self.walk_right if self.facing_right else self.walk_left
            return frames[self.frame_index]
        return self.idle_right if self.facing_right else self.idle_left