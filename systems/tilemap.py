import json
import os
import pygame

TILE = 16
SCALE = 4
FLIP_MASK = 0x1FFFFFFF


def index_to_cell(index, width):
    row = index // width
    col = index % width
    return row, col

def find_firstgid(gid, firstgids):
    best = None
    if gid <= 0:
        return None
    for f in firstgids:
        if f <= gid:
            best = f
    return best

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

def load_tilesets(data, json_path):
    map_folder = os.path.dirname(json_path)
    tilesets = {}
    for tileset in data["tilesets"]:
        sheet_path = f"assets/tiles/{tileset["source"][:-3]}png"
        tilesets[tileset["firstgid"]] = load_tiles(sheet_path)
    return tilesets

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

    for layer in data["layers"]:
        if layer["type"] != "tilelayer":
            continue
        if not layer.get("visible", True):
            continue

        name = layer["name"].lower()
        if name.startswith("collision"):
            continue
        target = above if name.startswith("above") else below

        for index, gid in enumerate(layer["data"]):
            gid = gid & FLIP_MASK
            if gid == 0:
                continue
            firstgid = find_firstgid(gid, firstgids)
            local = gid - firstgid
            row, col = index_to_cell(index, map_width)
            target.blit(tilesets[firstgid][local], (col * TILE * SCALE, row * TILE * SCALE))

    return below, above

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

def touches_solid(hitbox, solid):
    tile_size = TILE * SCALE
    left = hitbox.left // tile_size
    right = (hitbox.right - 1) // tile_size
    top = hitbox.top // tile_size
    bottom = (hitbox.bottom - 1) // tile_size

    for row in range(top, bottom + 1):
        for col in range(left, right + 1):
            if (col, row) in solid:
                return True
    return False