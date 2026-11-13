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


FUEL_COLOR = "#E8742C"
FUEL_ROW_GAP = 6


# "Fuel 1/3" under the coins, with a little fuel can drawn in code.
# Hidden until the first piece of fuel.
class FuelCounter:
    def __init__(self, top):
        self.font = pygame.font.Font(FONT_PATH, SMALL_FONT_SIZE)
        self.top = top
        size = COIN_ICON_HEIGHT
        self.icon = pygame.Surface((size, size), pygame.SRCALPHA)
        body = pygame.Rect(size // 6, size // 4, size * 2 // 3, size * 3 // 4)
        pygame.draw.rect(self.icon, FUEL_COLOR, body, border_radius=3)
        pygame.draw.rect(self.icon, "#000000", body, 2, border_radius=3)
        cap = pygame.Rect(body.right - size // 4, 0, size // 5, size // 4 + 2)
        pygame.draw.rect(self.icon, "#C9C9C9", cap)
        pygame.draw.line(self.icon, "#000000", (body.x + 5, body.y + 6),
                         (body.right - 5, body.bottom - 6), 2)

    def draw(self, screen, fuel, needed):
        if fuel <= 0:
            return
        icon_rect = self.icon.get_rect(topleft=(HUD_MARGIN, self.top))
        text = f"Fuel {fuel}/{needed}"
        label = self.font.render(text, False, TEXT_COLOR)
        shadow = self.font.render(text, False, "#000000")
        pos = label.get_rect(midleft=(icon_rect.right + COIN_GAP, icon_rect.centery))
        screen.blit(self.icon, icon_rect)
        screen.blit(shadow, pos.move(2, 2))
        screen.blit(label, pos)


OBJECTIVE_WIDTH = 330
OBJECTIVE_PADDING = 14
OBJECTIVE_DONE_COLOR = "#8A93AD"


# Bottom-right box showing the current quest. When the goal is reached the
# objective is greyed out and crossed out, with a hint to go turn it in.
class ObjectiveTracker:
    def __init__(self):
        self.title_font = pygame.font.Font(FONT_PATH, KEY_FONT_SIZE + 4)
        self.font = pygame.font.Font(FONT_PATH, KEY_FONT_SIZE)

    def draw(self, screen, quest):
        if quest is None:
            return
        rows = []   # (surface, strike through?)
        color = OBJECTIVE_DONE_COLOR if quest.complete else TEXT_COLOR
        text = quest.text
        if quest.goal > 1:
            text += f" ({min(quest.progress, quest.goal)}/{quest.goal})"
        rows.append((self.font.render(text, False, color), quest.complete))
        if quest.complete and quest.turn_in:
            rows.append((self.font.render("> " + quest.turn_in, False, TEXT_COLOR), False))

        title = self.title_font.render("Objective", False, "#F2C14E")
        height = (OBJECTIVE_PADDING * 2 + title.get_height() + 6
                  + sum(row.get_height() + 4 for row, _ in rows))
        width = max(OBJECTIVE_WIDTH, max(row.get_width() for row, _ in rows)
                    + OBJECTIVE_PADDING * 2)
        box = pygame.Rect(0, 0, width, height)
        box.bottomright = (SCREEN_WIDTH - HUD_MARGIN, SCREEN_HEIGHT - HUD_MARGIN)
        pygame.draw.rect(screen, BUTTON_FILL_COLOR, box, border_radius=KEY_RADIUS)
        pygame.draw.rect(screen, BUTTON_COLOR, box, width=2, border_radius=KEY_RADIUS)

        x = box.x + OBJECTIVE_PADDING
        y = box.y + OBJECTIVE_PADDING
        screen.blit(title, (x, y))
        y += title.get_height() + 6
        for row, strike in rows:
            screen.blit(row, (x, y))
            if strike:
                mid = y + row.get_height() // 2
                pygame.draw.line(screen, OBJECTIVE_DONE_COLOR, (x - 2, mid),
                                 (x + row.get_width() + 2, mid), 2)
            y += row.get_height() + 4
