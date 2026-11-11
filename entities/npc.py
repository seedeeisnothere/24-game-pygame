import pygame


# A character in the overworld the player can talk to (or shop with).
class NPC:
    def __init__(self, name, x, y, image_path, dialogue_id, portrait_path=None, shop_id=None):
        self.name = name
        self.dialogue_id = dialogue_id
        self.shop_id = shop_id

        self.image = pygame.transform.scale(
            pygame.image.load(image_path).convert_alpha(), (64, 87)
        )
        self.rect = self.image.get_rect(topleft=(x, y))

        # Feet hitbox like the player's; used for collision and talk range
        self.hitbox = pygame.Rect(0, 0, 40, 36)
        self.hitbox.midbottom = self.rect.midbottom

        self.portrait = None
        if portrait_path:
            self.portrait = pygame.image.load(portrait_path).convert_alpha()

    # True if the player is within `reach` pixels of the NPC's feet.
    def can_interact(self, player_hitbox, reach=24):
        return self.hitbox.inflate(reach * 2, reach * 2).colliderect(player_hitbox)

    # True if the mouse is over the NPC.
    def is_clicked(self, mouse_pos, cam_x, cam_y):
        # Convert screen mouse position to world position
        return self.rect.collidepoint(mouse_pos[0] + cam_x, mouse_pos[1] + cam_y)

    def draw(self, screen, cam_x, cam_y):
        screen.blit(self.image, (self.rect.x - cam_x, self.rect.y - cam_y))
