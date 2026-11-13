import pygame

GUN_IMAGE_PATH = "assets/item_assets/Gun.png"
GUN_SIZE = (44, 44)
SHADOW_SIZE = (34, 10)
SHADOW_ALPHA = 70


# The gun lying on the ground near the wreck. Walking into it picks it up.
class GunPickup:
    # (x, y) is the center of the gun in the world.
    def __init__(self, x, y):
        image = pygame.image.load(GUN_IMAGE_PATH).convert_alpha()
        self.image = pygame.transform.scale(image, GUN_SIZE)
        self.rect = self.image.get_rect(center=(x, y))
        self.shadow = pygame.Surface(SHADOW_SIZE, pygame.SRCALPHA)
        pygame.draw.ellipse(self.shadow, (0, 0, 0, SHADOW_ALPHA), self.shadow.get_rect())

    # Y value used to sort drawing order (things lower on screen draw on top).
    @property
    def sort_y(self):
        return self.rect.bottom

    # True if the player's feet hitbox touches the gun.
    def touches(self, hitbox):
        return self.rect.colliderect(hitbox)

    def draw(self, screen, cam_x, cam_y):
        shadow_pos = (self.rect.centerx - cam_x, self.rect.bottom - 6 - cam_y)
        screen.blit(self.shadow, self.shadow.get_rect(center=shadow_pos))
        screen.blit(self.image, (self.rect.x - cam_x, self.rect.y - cam_y))
