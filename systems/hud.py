import pygame
from settings import *
from systems.icons import load_icon

BAG_ICON_PATH = "assets/ui_assets/Bag.png"
BAG_ICON_HEIGHT = 48
HUD_MARGIN = 12
KEY_GAP = 8
KEY_PADDING = 7
KEY_FONT_SIZE = 16
KEY_RADIUS = 6


# Bottom-left hint: a bag icon above a key label (e.g. "SPACE").
class MenuHint:
    def __init__(self, key_label="SPACE"):
        # Scale the bag icon to a fixed height, keeping its aspect ratio
        image = pygame.image.load(BAG_ICON_PATH).convert_alpha()
        width = round(image.get_width() * BAG_ICON_HEIGHT / image.get_height())
        self.icon = pygame.transform.scale(image, (width, BAG_ICON_HEIGHT))

        font = pygame.font.Font(FONT_PATH, KEY_FONT_SIZE)
        self.label = font.render(key_label, False, TEXT_COLOR)
        self.key_rect = self.label.get_rect()
        self.key_rect.inflate_ip(KEY_PADDING * 2, KEY_PADDING * 2)

        # Center the icon and key box on the same vertical line
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


HP_BAR_POS = (HUD_MARGIN, HUD_MARGIN)
HP_BAR_SIZE = (260, 30)
HP_FILL_COLOR = "#C0392B"
HP_LOW_COLOR = "#E0524A"
HP_LERP_SPEED = 6.0
COIN_ROW_GAP = 10


# Top-left HP bar. The fill slides smoothly toward the real HP.
class HealthBar:
    def __init__(self):
        self.font = pygame.font.Font(FONT_PATH, KEY_FONT_SIZE + 4)
        self.rect = pygame.Rect(HP_BAR_POS, HP_BAR_SIZE)
        # The HP ratio currently drawn (None until the first draw)
        self.shown = None

    # Draw the bar. dt controls how fast the fill catches up.
    def draw(self, screen, hp, max_hp, dt=1 / FPS):
        ratio = hp / max_hp if max_hp else 0
        if self.shown is None:
            self.shown = ratio
        # Lerp: move a fraction of the remaining distance each frame
        self.shown += (ratio - self.shown) * min(1.0, HP_LERP_SPEED * dt)

        pygame.draw.rect(screen, BUTTON_FILL_COLOR, self.rect, border_radius=KEY_RADIUS)
        # Fill area is 4px inside the border on each side
        fill = self.rect.inflate(-8, -8)
        fill.width = round(fill.width * max(0.0, min(self.shown, 1.0)))
        if fill.width > 0:
            # Use a different colour at 30% HP or below
            color = HP_LOW_COLOR if ratio <= 0.3 else HP_FILL_COLOR
            pygame.draw.rect(screen, color, fill, border_radius=KEY_RADIUS - 2)
        pygame.draw.rect(screen, BUTTON_COLOR, self.rect, width=3, border_radius=KEY_RADIUS)

        # Text with a black drop shadow offset by 2px
        label = self.font.render(f"HP  {hp} / {max_hp}", False, TEXT_COLOR)
        shadow = self.font.render(f"HP  {hp} / {max_hp}", False, "#000000")
        pos = label.get_rect(midleft=(self.rect.x + 14, self.rect.centery))
        screen.blit(shadow, pos.move(2, 2))
        screen.blit(label, pos)

    @property
    def bottom(self):
        return self.rect.bottom


# Coin icon and amount, drawn just below the HP bar.
class CoinCounter:
    def __init__(self, top=HP_BAR_POS[1] + HP_BAR_SIZE[1] + COIN_ROW_GAP):
        self.icon = load_icon(COIN_ICON_PATH, COIN_ICON_HEIGHT)
        self.font = pygame.font.Font(FONT_PATH, SMALL_FONT_SIZE)
        self.top = top
        self.shown = None
        self.label = None

    def draw(self, screen, coins):
        # Only re-render the text when the coin count changes
        if coins != self.shown:
            self.shown = coins
            self.label = self.font.render(str(coins), False, TEXT_COLOR)
        icon_rect = self.icon.get_rect(topleft=(HUD_MARGIN, self.top))
        label_rect = self.label.get_rect(midleft=(icon_rect.right + COIN_GAP, icon_rect.centery))
        screen.blit(self.icon, icon_rect)
        screen.blit(self.label, label_rect)
