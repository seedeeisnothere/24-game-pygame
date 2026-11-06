import pygame
from settings import *

BAG_ICON_PATH = "assets/ui_assets/Bag.png"
BAG_ICON_HEIGHT = 48
HUD_MARGIN = 12
KEY_GAP = 8
KEY_PADDING = 7
KEY_FONT_SIZE = 16
KEY_RADIUS = 6


class MenuHint:
    def __init__(self, key_label="SPACE"):
        image = pygame.image.load(BAG_ICON_PATH).convert_alpha()
        width = round(image.get_width() * BAG_ICON_HEIGHT / image.get_height())
        self.icon = pygame.transform.scale(image, (width, BAG_ICON_HEIGHT))

        font = pygame.font.Font(FONT_PATH, KEY_FONT_SIZE)
        self.label = font.render(key_label, False, TEXT_COLOR)
        self.key_rect = self.label.get_rect()
        self.key_rect.inflate_ip(KEY_PADDING * 2, KEY_PADDING * 2)

        group_width = max(self.icon.get_width(), self.key_rect.width)
        center_x = HUD_MARGIN + group_width // 2
        self.key_rect.midbottom = (center_x, SCREEN_HEIGHT - HUD_MARGIN)
        self.label_rect = self.label.get_rect(center=self.key_rect.center)
        self.icon_rect = self.icon.get_rect(midbottom=(center_x, self.key_rect.top - KEY_GAP))

    def draw(self, screen):
        screen.blit(self.icon, self.icon_rect)
        pygame.draw.rect(screen, BUTTON_FILL_COLOR, self.key_rect, border_radius=KEY_RADIUS)
        pygame.draw.rect(screen, BUTTON_COLOR, self.key_rect, width=2, border_radius=KEY_RADIUS)
        screen.blit(self.label, self.label_rect)