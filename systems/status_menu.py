import pygame
from settings import *
from systems.icons import load_icon

HP_COLOR = "#C0392B"
DIM_COLOR = "#5A6480"
MAX_ROWS = 5


# Status window: HP, damage, potions, equipment slots and items
class StatusMenu:

    def __init__(self, game):
        self.game = game
        self.is_open = False
        self.message = ""
        self.message_timer = 0.0

        self.big_font = pygame.font.Font(FONT_PATH, BUTTON_FONT_SIZE)
        self.small_font = pygame.font.Font(FONT_PATH, SMALL_FONT_SIZE)
        self.tiny_font = pygame.font.Font(FONT_PATH, CREDITS_FONT_SIZE)

        # Dark see-through layer behind the panel
        self.dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.dim.fill((0, 0, 0, 170))
        self.panel = pygame.Rect(140, 80, 1000, 640)
        self.hp_bar = pygame.Rect(180, 230, 440, 44)

        # One square box per equipment slot, in a row
        slot_count = len(game.state.inventory.equipped)
        self.slot_rects = [pygame.Rect(180 + i * 150, 430, 130, 130) for i in range(slot_count)]
        # Item list on the right side
        self.row_rects = [pygame.Rect(680, 250 + i * 92, 420, 84) for i in range(MAX_ROWS)]
        self.potion_icon = load_icon(POTION_ICON_PATH, 36)
        self.skip_icon = load_icon(SKIP_ICON_PATH, 28)

    def open(self):
        self.is_open = True
        self.message_timer = 0.0

    def close(self):
        self.is_open = False

    # Show a red message at the bottom for 1.5 seconds
    def show(self, text):
        self.message = text
        self.message_timer = 1.5

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_ESCAPE):
            self.close()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.click(event.pos)

    # Click a slot to unequip, or an item to equip/unequip it
    def click(self, pos):
        inventory = self.game.state.inventory
        for slot, rect in enumerate(self.slot_rects):
            if rect.collidepoint(pos):
                inventory.unequip(slot)
                return
        for item_id, rect in zip(inventory.owned, self.row_rects):
            if rect.collidepoint(pos):
                if item_id in inventory.equipped:
                    inventory.unequip(inventory.equipped.index(item_id))
                elif not inventory.equip(item_id):
                    self.show("Slots full")
                return

    # Count down the message timer
    def update(self, dt):
        self.message_timer = max(0.0, self.message_timer - dt)

    # Render text and place it with a rect anchor like topleft=(x, y)
    def text(self, screen, font, string, color, **anchor):
        surface = font.render(string, False, color)
        screen.blit(surface, surface.get_rect(**anchor))

    # Draw a filled rounded box with a coloured border
    def draw_box(self, screen, rect, border_color):
        pygame.draw.rect(screen, BUTTON_FILL_COLOR, rect, border_radius=BUTTON_RADIUS)
        pygame.draw.rect(screen, border_color, rect, width=4, border_radius=BUTTON_RADIUS)

    # Draw the whole status window
    def draw(self, screen):
        if not self.is_open:
            return
        state = self.game.state
        inventory = state.inventory
        mouse = pygame.mouse.get_pos()

        screen.blit(self.dim, (0, 0))
        pygame.draw.rect(screen, PANEL_COLOR, self.panel, border_radius=BUTTON_RADIUS)
        pygame.draw.rect(screen, BUTTON_COLOR, self.panel, width=5, border_radius=BUTTON_RADIUS)
        self.text(screen, self.big_font, "Status", TEXT_COLOR, topleft=(180, 110))

        # HP bar: grey track, red fill sized by hp / max_hp, white border
        self.text(screen, self.small_font, "HP", TEXT_COLOR, topleft=(180, 190))
        pygame.draw.rect(screen, SLIDER_TRACK_COLOR, self.hp_bar)
        fill = self.hp_bar.copy()
        fill.width = int(self.hp_bar.width * state.hp / state.max_hp)
        pygame.draw.rect(screen, HP_COLOR, fill)
        pygame.draw.rect(screen, TEXT_COLOR, self.hp_bar, 3)
        self.text(screen, self.small_font, f"{state.hp} / {state.max_hp}", TEXT_COLOR, center=self.hp_bar.center)

        damage_text = f"Damage  {state.base_damage}"
        screen.blit(self.potion_icon, (180, 343))
        self.text(screen, self.small_font, f"Heal Potion  x{state.potions}", TEXT_COLOR,
                  topleft=(180 + self.potion_icon.get_width() + 12, 345))
        screen.blit(self.skip_icon, (480, 347))
        self.text(screen, self.small_font, f"Skip x{state.skips}", TEXT_COLOR,
                  topleft=(480 + self.skip_icon.get_width() + 12, 345))
        # Show bonus damage from equipment, if any
        if state.damage_bonus:
            damage_text += f"  (+{state.damage_bonus})"
        self.text(screen, self.small_font, damage_text, TEXT_COLOR, topleft=(180, 305))

        self.text(screen, self.small_font, "Equipment", TEXT_COLOR, topleft=(180, 385))
        for rect, item_id in zip(self.slot_rects, inventory.equipped):
            self.draw_box(screen, rect, BUTTON_HOVER_COLOR if rect.collidepoint(mouse) else BUTTON_COLOR)
            if item_id is None:
                self.text(screen, self.tiny_font, "Empty", DIM_COLOR, center=rect.center)
                continue
            # One word per line, centred vertically (28 px line height)
            lines = inventory.items[item_id]["name"].split(" ")
            top = rect.centery - len(lines) * 14
            for n, line in enumerate(lines):
                self.text(screen, self.tiny_font, line, TEXT_COLOR, center=(rect.centerx, top + 14 + n * 28))

        hover_desc = None
        self.text(screen, self.small_font, "Items", TEXT_COLOR, topleft=(680, 200))
        if not inventory.owned:
            self.text(screen, self.tiny_font, "No items yet", DIM_COLOR, topleft=(680, 260))
        for item_id, rect in zip(inventory.owned, self.row_rects):
            item = inventory.items[item_id]
            equipped = item_id in inventory.equipped
            hovered = rect.collidepoint(mouse)
            self.draw_box(screen, rect, BUTTON_HOVER_COLOR if hovered else BUTTON_COLOR)
            name_color = DIM_COLOR if equipped else TEXT_COLOR
            self.text(screen, self.small_font, item["name"], name_color, topleft=(rect.x + 16, rect.y + 8))
            # The row only fits the last desc line (the effect); hover shows the rest below
            desc_lines = [line.strip() for line in item["desc"].split("\n")]
            self.text(screen, self.tiny_font, desc_lines[-1], DIM_COLOR, topleft=(rect.x + 16, rect.y + 50))
            if hovered and len(desc_lines) > 1:
                hover_desc = " ".join(desc_lines[:-1])
            if equipped:
                self.text(screen, self.tiny_font, "Equipped", BUTTON_HOVER_COLOR,
                          midright=(rect.right - 16, rect.y + 24))

        if self.message_timer > 0:
            self.text(screen, self.small_font, self.message, "#E0524A", midbottom=(640, 655))
        elif hover_desc:
            self.text(screen, self.tiny_font, hover_desc, TEXT_COLOR, midbottom=(640, 655))
        self.text(screen, self.tiny_font, "Click item = equip / remove     Click slot = remove     Space = close",
                  DIM_COLOR, midbottom=(640, 700))
