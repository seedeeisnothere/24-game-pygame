import json
import pygame
from settings import *
from systems.icons import load_icon

# Size of one map tile on the minimap, in pixels
CELL = 3
# Size of one tile on the big map (opened with M)
BIG_CELL = 13
PADDING = 8
MARGIN = 12
PANEL_COLOR_RGBA = (8, 10, 18, 215)
PANEL_BORDER = BUTTON_COLOR

# Tiled layer names (in Thai) that hold grass/dirt/water ground tiles
GROUND_LAYERS = ["พิ้นน้ำ และน้ำ", "น้ำตก"]
HOUSE_LAYER = "บ้าน"
BUILDING_TILESET = "Buildings"
GROUND_SHEET = "assets/tiles/seasonal sample (spring).png"
TILE = 16

# Fill and outline colour (RGBA) for each kind of cell
STYLES = {
    "dirt":     ((255, 255, 255, 22),    (225, 232, 245, 150)),
    "water":    ((70, 140, 210, 70),     (120, 185, 240, 200)),
    "building": ((225, 232, 245, 80),    (240, 244, 255, 235)),
    "solid":    ((255, 255, 255, 45),    None),
}
# Solid style with an outline, used for cave maps
SOLID_OUTLINED = ((255, 255, 255, 40),  (225, 232, 245, 170))
# Kinds drawn later appear on top
DRAW_ORDER = ["dirt", "water", "solid", "building"]

PLAYER_COLOR = "#FFFFFF"
PLAYER_DOT_RADIUS = 4
DIM_ALPHA = 170
BOSS_COLOR = "#E0524A"
SHOP_ICON_SIZE = 16
# Seconds for one boss ring pulse
PULSE_PERIOD = 1.2


# Guess if a tile is water or dirt from its average colour
def classify_color(color):
    r, g, b = color[:3]
    if b > r + 20 and b >= g - 10:
        return "water"
    if r > g + 10:
        return "dirt"
    return None


# Read a Tiled map and sort its cells into dirt/water/building/solid
def read_grid(map_path, water_layers=()):
    with open(map_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    width, height = data["width"], data["height"]
    firstgids = sorted((ts["firstgid"], ts["source"]) for ts in data["tilesets"])

    # Find which tileset file a tile id belongs to
    def tileset_of(gid):
        name = None
        for firstgid, source in firstgids:
            if firstgid <= gid:
                name = source
        return name

    sheet = pygame.image.load(GROUND_SHEET)
    sheet_cols = sheet.get_width() // TILE
    color_cache = {}

    # Classify a ground tile once, then remember the answer
    def ground_kind(gid):
        if gid not in color_cache:
            local = gid - 1
            rect = pygame.Rect((local % sheet_cols) * TILE, (local // sheet_cols) * TILE, TILE, TILE)
            color_cache[gid] = classify_color(pygame.transform.average_color(sheet, rect))
        return color_cache[gid]

    cells = {kind: set() for kind in STYLES}
    for layer in data["layers"]:
        if layer["type"] != "tilelayer":
            continue
        name = layer["name"]
        for index, raw in enumerate(layer["data"]):
            # Remove Tiled's flip flags from the top bits
            gid = raw & 0x1FFFFFFF
            if not gid:
                continue
            cell = (index % width, index // width)
            if name in GROUND_LAYERS and tileset_of(gid).startswith("seasonal"):
                # Later ground layers replace earlier ones
                kind = ground_kind(gid)
                cells["dirt"].discard(cell)
                cells["water"].discard(cell)
                if kind:
                    cells[kind].add(cell)
            elif name in water_layers:
                cells["water"].add(cell)
            elif name == HOUSE_LAYER and tileset_of(gid).startswith(BUILDING_TILESET):
                cells["building"].add(cell)
            elif name.lower().startswith("collision"):
                cells["solid"].add(cell)
    # Buildings and water are already drawn, so don't count them as solid
    cells["solid"] -= cells["building"] | cells["water"]
    return width, height, cells


# Fill each cell, then draw edges only where a neighbour is missing
def draw_cells(surface, cells, fill, outline, cell=CELL):
    for col, row in cells:
        if fill:
            surface.fill(fill, (col * cell, row * cell, cell, cell))
    if not outline:
        return
    line = max(1, cell // 6)
    for col, row in cells:
        x, y = col * cell, row * cell
        if (col, row - 1) not in cells:
            surface.fill(outline, (x, y, cell, line))
        if (col, row + 1) not in cells:
            surface.fill(outline, (x, y + cell - line, cell, line))
        if (col - 1, row) not in cells:
            surface.fill(outline, (x, y, line, cell))
        if (col + 1, row) not in cells:
            surface.fill(outline, (x + cell - line, y, line, cell))


# Draw the whole map onto a rounded panel and return it
def build_panel(cols, rows, cells, cell, padding, background=PANEL_COLOR_RGBA, styles=STYLES):
    map_size = (cols * cell, rows * cell)
    map_layer = pygame.Surface(map_size, pygame.SRCALPHA)
    for kind in DRAW_ORDER:
        fill, outline = styles[kind]
        draw_cells(map_layer, cells[kind], fill, outline, cell)
    pygame.draw.rect(map_layer, (225, 232, 245, 110), map_layer.get_rect(), 1)

    panel = pygame.Surface((map_size[0] + padding * 2, map_size[1] + padding * 2), pygame.SRCALPHA)
    pygame.draw.rect(panel, background, panel.get_rect(), border_radius=10)
    pygame.draw.rect(panel, PANEL_BORDER, panel.get_rect(), width=2, border_radius=10)
    panel.blit(map_layer, (padding, padding))
    return panel


# One map size (small corner or big centre) plus world-to-screen math
class MapView:

    # anchor is a rect position like topright=(x, y) or center=(x, y)
    def __init__(self, cols, rows, cells, cell, padding, world_size, background=PANEL_COLOR_RGBA,
                 styles=STYLES, **anchor):
        self.panel = build_panel(cols, rows, cells, cell, padding, background, styles)
        self.rect = self.panel.get_rect(**anchor)
        # The map area inside the panel padding
        self.area = pygame.Rect(self.rect.x + padding, self.rect.y + padding, cols * cell, rows * cell)
        # Screen pixels per world pixel
        self.scale = (self.area.width / world_size[0], self.area.height / world_size[1])
        # Markers are drawn bigger on the big map
        self.marker_scale = 1.0 if cell == CELL else 1.6

    # Convert a world position to a screen position, clamped to the map
    def to_screen(self, world_x, world_y):
        x = self.area.x + world_x * self.scale[0]
        y = self.area.y + world_y * self.scale[1]
        return (max(self.area.left, min(x, self.area.right)), max(self.area.top, min(y, self.area.bottom)))


# Corner minimap that can expand into a big map with M
class Minimap:

    def __init__(self, map_path, world_size, water_layers=(), outline_solid=False):
        cols, rows, cells = read_grid(map_path, water_layers)
        styles = dict(STYLES, solid=SOLID_OUTLINED) if outline_solid else STYLES
        self.small = MapView(cols, rows, cells, CELL, PADDING, world_size, styles=styles,
                             topright=(SCREEN_WIDTH - MARGIN, MARGIN))
        self.big = MapView(cols, rows, cells, BIG_CELL, PADDING * 2, world_size, background=(8, 10, 18, 255),
                           styles=styles, center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.rect = self.small.rect
        self.expanded = False

        # Dark see-through layer behind the big map
        self.dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.dim.fill((0, 0, 0, DIM_ALPHA))
        self.font = pygame.font.Font(FONT_PATH, CREDITS_FONT_SIZE)
        self.key_font = pygame.font.Font(FONT_PATH, 16)
        # Shop icons for each marker scale (small map, big map)
        self.shop_icons = {1.0: load_icon(COIN_ICON_PATH, SHOP_ICON_SIZE),
                           1.6: load_icon(COIN_ICON_PATH, round(SHOP_ICON_SIZE * 1.6))}
        # Running clock for the boss pulse animation
        self.time = 0.0

    def toggle(self):
        self.expanded = not self.expanded

    def close(self):
        self.expanded = False

    # Close the big map with M or Esc
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_m, pygame.K_ESCAPE):
            self.close()

    def update(self, dt):
        self.time += dt

    # Draw a coin icon in a gold circle; k is the marker scale
    def draw_shop(self, screen, pos, k):
        icon = self.shop_icons[k]
        radius = icon.get_height() // 2 + round(3 * k)
        pygame.draw.circle(screen, "#000000", pos, radius)
        pygame.draw.circle(screen, "#F2C14E", pos, radius, max(1, round(k)))
        screen.blit(icon, icon.get_rect(center=pos))

    # Draw a red diamond with a growing, fading ring
    def draw_boss(self, screen, pos, k):
        # pulse goes 0 -> 1 every PULSE_PERIOD seconds
        pulse = (self.time % PULSE_PERIOD) / PULSE_PERIOD
        ring_size = round(40 * k)
        ring = pygame.Surface((ring_size, ring_size), pygame.SRCALPHA)
        # Ring gets bigger and more transparent as pulse grows
        pygame.draw.circle(ring, (224, 82, 74, round(160 * (1 - pulse))), (ring_size // 2, ring_size // 2),
                           round((6 + 12 * pulse) * k), 2)
        screen.blit(ring, ring.get_rect(center=pos))
        x, y = pos
        size = 7 * k
        diamond = [(x, y - size), (x + size, y), (x, y + size), (x - size, y)]
        pygame.draw.polygon(screen, BOSS_COLOR, diamond)
        pygame.draw.polygon(screen, "#FFFFFF", diamond, 2)

    # Draw the player as a white dot with a black border
    def draw_player(self, screen, pos, k):
        radius = round(PLAYER_DOT_RADIUS * k)
        pygame.draw.circle(screen, "#000000", pos, radius + 1)
        pygame.draw.circle(screen, PLAYER_COLOR, pos, radius)

    # Draw a text label with a shadow just below a marker
    def label(self, screen, text, pos):
        surface = self.font.render(text, False, TEXT_COLOR)
        shadow = self.font.render(text, False, "#000000")
        rect = surface.get_rect(midtop=(pos[0], pos[1] + 18))
        screen.blit(shadow, rect.move(2, 2))
        screen.blit(surface, rect)

    # Draw shop, boss and player markers on a map view
    def draw_markers(self, screen, view, player_center, shops, bosses, labels=False):
        k = view.marker_scale
        for world_pos in shops:
            pos = view.to_screen(*world_pos)
            self.draw_shop(screen, pos, k)
            if labels:
                self.label(screen, "Shop", pos)
        for world_pos in bosses:
            pos = view.to_screen(*world_pos)
            self.draw_boss(screen, pos, k)
            if labels:
                self.label(screen, "Boss", pos)
        # Player is drawn last so it is always on top
        pos = view.to_screen(*player_center)
        self.draw_player(screen, pos, k)
        if labels:
            self.label(screen, "You", pos)

    # Draw a small "M" key box in the minimap corner
    def draw_key_hint(self, screen):
        text = self.key_font.render("M", False, TEXT_COLOR)
        box = text.get_rect().inflate(12, 8)
        box.bottomright = (self.small.rect.right - 6, self.small.rect.bottom - 6)
        pygame.draw.rect(screen, BUTTON_FILL_COLOR, box, border_radius=5)
        pygame.draw.rect(screen, BUTTON_COLOR, box, width=2, border_radius=5)
        screen.blit(text, text.get_rect(center=box.center))

    # Draw the small minimap in the top-right corner
    def draw(self, screen, player_center, shops=(), bosses=()):
        if self.expanded:
            return
        screen.blit(self.small.panel, self.small.rect)
        self.draw_markers(screen, self.small, player_center, shops, bosses)
        self.draw_key_hint(screen)

    # Draw the big centred map when it is open
    def draw_expanded(self, screen, player_center, shops=(), bosses=()):
        if not self.expanded:
            return
        screen.blit(self.dim, (0, 0))
        screen.blit(self.big.panel, self.big.rect)
        self.draw_markers(screen, self.big, player_center, shops, bosses, labels=True)
        hint = self.font.render("M / Esc = close", False, "#9AA3BD")
        screen.blit(hint, hint.get_rect(midtop=(SCREEN_WIDTH // 2, self.big.rect.bottom + 8)))
