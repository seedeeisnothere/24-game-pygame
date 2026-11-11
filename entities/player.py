import os
import pygame


# Holds idle and walking frames and picks the right one each frame.
# Used by the player and by enemies.
class AnimatedSprite:
    def __init__(self, idle_path, walk_paths, frame_duration_ms=75,
                 size=(64, 87), walk_dir="assets/sprites/player/walk"):
        # Load an image and scale it to the sprite size
        def load(path):
            image = pygame.image.load(path).convert_alpha()
            return pygame.transform.scale(image, size)

        self.idle_right = load(idle_path)
        self.walk_right = [load(os.path.join(walk_dir, p)) for p in walk_paths]

        # Flipped copies made once, so we never flip inside the game loop
        self.idle_left = pygame.transform.flip(self.idle_right, True, False)
        self.walk_left = [pygame.transform.flip(f, True, False) for f in self.walk_right]

        self.frame_duration_ms = frame_duration_ms
        self.frame_index = 0
        self.timer = 0.0
        self.frame_duration = self.frame_duration_ms / 1000   # ms -> seconds, like dt
        self.moving = False
        self.facing_right = True

    # Advance the walk animation using the frame time dt.
    def update(self, dt):
        if not self.moving:
            # Reset so the next walk starts from the first frame
            self.frame_index = 0
            self.timer = 0.0
            return

        self.timer += dt
        if self.timer >= self.frame_duration:
            self.timer -= self.frame_duration    # keep the leftover time
            # Wrap around to frame 0 after the last frame
            self.frame_index = (self.frame_index + 1) % len(self.walk_right)

    # Return the image to draw, based on moving and facing direction.
    def get_image(self):
        if self.moving:
            frames = self.walk_right if self.facing_right else self.walk_left
            return frames[self.frame_index]
        return self.idle_right if self.facing_right else self.idle_left
