import json
import pygame

# Tile size in the image files, and how much we enlarge them
TILE = 16
SCALE = 4
# Tiled stores flip info in the top 3 bits of each tile id
FLIP_H = 0x80000000
FLIP_V = 0x40000000
FLIP_D = 0x20000000
# Mask that removes the flip bits, leaving the real tile id
FLIP_MASK = 0x1FFFFFFF


# Flip/rotate a tile image to match Tiled's flip flags
def apply_flips(tile, flags):
    # Diagonal flip = rotate 90 degrees then flip vertically
    if flags & FLIP_D:
        tile = pygame.transform.flip(pygame.transform.rotate(tile, 90), False, True)
    if flags & FLIP_H or flags & FLIP_V:
        tile = pygame.transform.flip(tile, bool(flags & FLIP_H), bool(flags & FLIP_V))
    return tile


# Turn a flat list index into (row, col) on the map grid
def index_to_cell(index, width):
    row = index // width
    col = index % width
    return row, col


# Find which tileset a tile id belongs to (largest firstgid <= gid)
def find_firstgid(gid, firstgids):
    best = None
    if gid <= 0:
        return None
    for firstgid in firstgids:
        if firstgid <= gid:
            best = firstgid
    return best


# Cut a sprite sheet into a list of scaled-up tiles
def load_tiles(sheet_path):
    sheet = pygame.image.load(sheet_path).convert_alpha()
    columns = sheet.get_width() // TILE
    rows = sheet.get_height() // TILE
    tiles = []
    for row in range(rows):
        for col in range(columns):
            rect = pygame.Rect(col * TILE, row * TILE, TILE, TILE)
            tile = sheet.subsurface(rect)
            tile = pygame.transform.scale(tile, (TILE * SCALE, TILE * SCALE))
            tiles.append(tile)
    return tiles


# Load every tileset in the map as {firstgid: list of tiles}
def load_tilesets(data, json_path):
    tilesets = {}
    for tileset in data["tilesets"]:
        # "name.tsx" -> "assets/tiles/name.png"
        sheet_path = f"assets/tiles/{tileset["source"][:-3]}png"
        tilesets[tileset["firstgid"]] = load_tiles(sheet_path)
    return tilesets


# Read a gate layer: returns its tile images and its hitboxes
def read_gate(layer, name, map_width, tilesets, firstgids):
    tiles = []
    rects = []
    tile_size = TILE * SCALE

    for index, raw_gid in enumerate(layer["data"]):
        gid = raw_gid & FLIP_MASK
        if gid == 0:
            continue
        row, col = index_to_cell(index, map_width)
        position = (col * tile_size, row * tile_size)
        rects.append(pygame.Rect(position, (tile_size, tile_size)))
        # "gate_wall" layers are invisible blockers, so no image needed
        if name.startswith("gate_wall"):
            continue
        firstgid = find_firstgid(gid, firstgids)
        tile = tilesets[firstgid][gid - firstgid]
        flags = raw_gid & ~FLIP_MASK
        if flags:
            tile = apply_flips(tile, flags)
        tiles.append((tile, position))
    return tiles, rects


# Draw the map into two big images (below and above the player) plus gates
def load_map(json_path):
    with open(json_path, "r") as file:
        data = json.load(file)

    map_width = data["width"]
    map_height = data["height"]
    tilesets = load_tilesets(data, json_path)
    firstgids = list(tilesets.keys())

    size = (map_width * TILE * SCALE, map_height * TILE * SCALE)
    below = pygame.Surface(size, pygame.SRCALPHA)
    above = pygame.Surface(size, pygame.SRCALPHA)
    # Reuse flipped tiles instead of flipping again
    flip_cache = {}
    gates = []

    for layer in data["layers"]:
        if layer["type"] != "tilelayer":
            continue

        name = layer["name"].lower()
        if name.startswith("gate"):
            gates.append(read_gate(layer, name, map_width, tilesets, firstgids))
            continue
        if not layer.get("visible", True):
            continue
        if name.startswith("collision"):
            continue
        # Layers named "above..." are drawn over the player
        target = above if name.startswith("above") else below

        for index, raw_gid in enumerate(layer["data"]):
            gid = raw_gid & FLIP_MASK
            if gid == 0:
                continue
            flags = raw_gid & ~FLIP_MASK
            firstgid = find_firstgid(gid, firstgids)
            # Tile's position inside its own tileset
            local = gid - firstgid
            row, col = index_to_cell(index, map_width)
            tile = tilesets[firstgid][local]
            if flags:
                key = (firstgid, local, flags)
                if key not in flip_cache:
                    flip_cache[key] = apply_flips(tile, flags)
                tile = flip_cache[key]
            target.blit(tile, (col * TILE * SCALE, row * TILE * SCALE))

    return below, above, gates


# Return a set of (col, row) cells from the "collision" layers
def load_collision(json_path):
    with open(json_path, "r") as file:
        data = json.load(file)

    map_width = data["width"]
    solid = set()

    for layer in data["layers"]:
        if layer["type"] != "tilelayer":
            continue
        if not layer["name"].lower().startswith("collision"):
            continue

        for index, gid in enumerate(layer["data"]):
            gid = gid & FLIP_MASK
            if gid == 0:
                continue
            row, col = index_to_cell(index, map_width)
            solid.add((col, row))

    return solid


# Check if a hitbox overlaps any solid tile
def touches_solid(hitbox, solid):
    tile_size = TILE * SCALE
    # Tiles covered by the hitbox; -1 so an exact edge doesn't count
    left = hitbox.left // tile_size
    right = (hitbox.right - 1) // tile_size
    top = hitbox.top // tile_size
    bottom = (hitbox.bottom - 1) // tile_size

    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            if (col, row) in solid:
                return True
    return False
