import pygame


class NPC:
    def __init__(self, name, x, y, image_path, dialogue_id, portrait_path=None):
        self.name = name
        self.dialogue_id = dialogue_id

        self.image = pygame.transform.scale(
            pygame.image.load(image_path).convert_alpha(), (64, 87)
        )
        self.rect = self.image.get_rect(topleft=(x, y))

        # hitbox ที่เท้า เหมือนฝั่งผู้เล่น ใช้ทั้งชนและเช็คระยะ interact
        self.hitbox = pygame.Rect(0, 0, 40, 36)
        self.hitbox.midbottom = self.rect.midbottom

        self.portrait = None
        if portrait_path:
            self.portrait = pygame.image.load(portrait_path).convert_alpha()

    def can_interact(self, player_hitbox, reach=24):
        return self.hitbox.inflate(reach * 2, reach * 2).colliderect(player_hitbox)

    def draw(self, screen, cam_x, cam_y):
        screen.blit(self.image, (self.rect.x - cam_x, self.rect.y - cam_y))