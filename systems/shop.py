import json
import pygame
from settings import *
from systems.icons import load_icon

SHOP_PATH = "data/shop.json"
# Consumables are not in the inventory item list. They're kept as a count on
# the game state (e.g. state.potions) and never sell out.
CONSUMABLES = {
    "potion": {"name": "Heal Potion", "desc": "Use in battle to heal",
               "count": "potions", "icon": POTION_ICON_PATH},
    "skip": {"name": "Skip Ticket", "desc": "Use in battle to skip a 24 puzzle",
             "count": "skips", "icon": SKIP_ICON_PATH},
}

DIM_COLOR = "#5A6480"
ERROR_COLOR = "#E0524A"
OK_COLOR = "#6FCF6F"
MAX_ROWS = 6


# Load all shops as {shop_id: {"title": ..., "stock": [...]}}
def load_shops(path=SHOP_PATH):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


# Buying logic, kept separate from the UI so it can be tested
class Shop:

    def __init__(self, title, stock):
        self.title = title
        self.stock = stock

    # Get the name and description of a stock entry
    def info(self, state, entry):
        if entry["item"] in CONSUMABLES:
            return CONSUMABLES[entry["item"]]
        return state.inventory.items[entry["item"]]

    # Equipment can be bought once; consumables can be bought forever
    def is_sold_out(self, state, entry):
        return entry["item"] not in CONSUMABLES and entry["item"] in state.inventory.owned

    # Try to buy an entry; returns "bought", "owned" or "no_coins"
    def buy(self, state, entry):
        if self.is_sold_out(state, entry):
            return "owned"
        if not state.spend_coins(entry["price"]):
            return "no_coins"
        consumable = CONSUMABLES.get(entry["item"])
        if consumable:
            count = consumable["count"]
            setattr(state, count, getattr(state, count) + 1)
        else:
            state.inventory.add(entry["item"])
        return "bought"


# Shop window drawn over the overworld
class ShopMenu:

    def __init__(self, game, shops=None):
        self.game = game
        self.shops = shops if shops is not None else load_shops()
        self.shop = None
        self.is_open = False
        self.message = ""
        self.message_color = TEXT_COLOR
        self.message_timer = 0.0

        self.big_font = pygame.font.Font(FONT_PATH, BUTTON_FONT_SIZE)
        self.small_font = pygame.font.Font(FONT_PATH, SMALL_FONT_SIZE)
        self.tiny_font = pygame.font.Font(FONT_PATH, CREDITS_FONT_SIZE)

        # Dark see-through layer behind the panel
        self.dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.dim.fill((0, 0, 0, 170))
        self.panel = pygame.Rect(140, 80, 1000, 640)
        # One clickable row per item, stacked 74 px apart
        self.row_rects = [pygame.Rect(180, 175 + i * 74, 920, 68) for i in range(MAX_ROWS)]
        self.coin_icon = load_icon(COIN_ICON_PATH, 32)
        self.consumable_icons = {item_id: load_icon(info["icon"], 44)
                                 for item_id, info in CONSUMABLES.items()}

    # Open the shop with the given id from shop.json
    def open(self, shop_id):
        data = self.shops.get(shop_id)
        if not data:
            print(f"[warn] shop not found: {shop_id}")
            return
        self.shop = Shop(data["title"], data["stock"])
        self.is_open = True
        self.message_timer = 0.0

    def close(self):
        self.is_open = False

    # Show a message at the bottom for 1.5 seconds
    def show(self, text, color):
        self.message = text
        self.message_color = color
        self.message_timer = 1.5

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_e):
            self.close()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.click(event.pos)

    # Buy the item in the row that was clicked
    def click(self, pos):
        state = self.game.state
        for entry, rect in zip(self.shop.stock, self.row_rects):
            if not rect.collidepoint(pos):
                continue
            name = self.shop.info(state, entry)["name"]
            result = self.shop.buy(state, entry)
            if result == "bought":
                # Upgrades (equipment) get a power-up sound; potions/tickets a plain click
                upgrade = entry["item"] not in CONSUMABLES
                self.game.play_sfx("powerup" if upgrade else "select")
                self.show(f"Bought {name}!", OK_COLOR)
            elif result == "owned":
                self.show("You already own that", ERROR_COLOR)
            else:
                self.show("Not enough coins", ERROR_COLOR)
            return

    # Count down the message timer
    def update(self, dt):
        self.message_timer = max(0.0, self.message_timer - dt)

    # Render text and place it with a rect anchor like topleft=(x, y)
    def text(self, screen, font, string, color, **anchor):
        surface = font.render(string, False, color)
        screen.blit(surface, surface.get_rect(**anchor))

    # Draw the shop panel, coins, item rows and messages
    def draw(self, screen):
        if not self.is_open:
            return
        state = self.game.state
        mouse = pygame.mouse.get_pos()

        screen.blit(self.dim, (0, 0))
        pygame.draw.rect(screen, PANEL_COLOR, self.panel, border_radius=BUTTON_RADIUS)
        pygame.draw.rect(screen, BUTTON_COLOR, self.panel, width=5, border_radius=BUTTON_RADIUS)
        self.text(screen, self.big_font, self.shop.title, TEXT_COLOR, topleft=(180, 110))

        # Player's coins in the top-right of the panel
        coin_rect = self.coin_icon.get_rect(topright=(1100, 124))
        screen.blit(self.coin_icon, coin_rect)
        self.text(screen, self.small_font, str(state.coins), TEXT_COLOR,
                  midright=(coin_rect.left - 10, coin_rect.centery))

        for entry, rect in zip(self.shop.stock, self.row_rects):
            info = self.shop.info(state, entry)
            sold_out = self.shop.is_sold_out(state, entry)
            affordable = state.coins >= entry["price"]
            hovered = rect.collidepoint(mouse) and not sold_out

            pygame.draw.rect(screen, BUTTON_FILL_COLOR, rect, border_radius=BUTTON_RADIUS)
            pygame.draw.rect(screen, BUTTON_HOVER_COLOR if hovered else BUTTON_COLOR, rect,
                             width=4, border_radius=BUTTON_RADIUS)

            # Consumables get an icon and a count, so shift the text right
            text_x = rect.x + 20
            icon = self.consumable_icons.get(entry["item"])
            if icon:
                # Icons sit centred in a fixed 64 px column so the names line up
                screen.blit(icon, icon.get_rect(center=(rect.x + 16 + 32, rect.centery)))
                text_x += 64 + 4
                info_name = f"{info['name']}  (have {getattr(state, info['count'])})"
            else:
                info_name = info["name"]

            name_color = DIM_COLOR if sold_out else TEXT_COLOR
            self.text(screen, self.small_font, info_name, name_color, topleft=(text_x, rect.y + 4))
            self.text(screen, self.tiny_font, info["desc"], DIM_COLOR, topleft=(text_x, rect.y + 38))

            # Right side: "Owned" or the price (red if too expensive)
            if sold_out:
                self.text(screen, self.small_font, "Owned", BUTTON_HOVER_COLOR,
                          midright=(rect.right - 24, rect.centery))
            else:
                icon_rect = self.coin_icon.get_rect(midright=(rect.right - 24, rect.centery))
                screen.blit(self.coin_icon, icon_rect)
                price_color = TEXT_COLOR if affordable else ERROR_COLOR
                self.text(screen, self.small_font, str(entry["price"]), price_color,
                          midright=(icon_rect.left - 10, rect.centery))

        if self.message_timer > 0:
            self.text(screen, self.small_font, self.message, self.message_color, midbottom=(640, 655))
        self.text(screen, self.tiny_font, "Click item = buy     E / Space / Esc = leave",
                  DIM_COLOR, midbottom=(640, 700))
