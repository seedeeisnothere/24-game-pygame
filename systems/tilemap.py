import json
import pygame
from game import *

TILE = 16
SCALE = 2


def index_to_cell(index, width):
    row = index // width
    col = index % width
    return row, col

def find_firstgid(gid, firstgids): 
    if gid <= 0:
        return None
    for f in firstgids:
        if f <= gid:
            best = f
    return best

def load_tiles(sheet_path):
    global screen
    sheet = pygame.image.load(sheet_path).convert_alpha()
    columns = sheet.get_width() // 16
    rows = sheet.get_height() // 16
    tiles = []
    for row in range(rows):
        for col in range(columns):
            rect = pygame.Rect(col * 16, row * 16, TILE, TILE)
            tile = sheet.subsurface(rect)
            tile = pygame.transform.scale(tile, (16 * SCALE, 16 * SCALE))
            tiles.append(tile)

    return tiles

def load_map(json_path, tiles):
    with open(json_path, "r") as file:
        data = json.load(file)

    map_width = data["width"]
    map_height = data["height"]
    firstgids = []
    for tileset in data["tilesets"]:
        firstgids.append(tileset["firstgid"])

    surface = pygame.Surface((map_width * 32, map_height * 32), pygame.SRCALPHA)

    for layer in data["layers"]:
        if layer["type"] != "tilelayer":
            continue
        for index, gid in enumerate(layer["data"]):
            if gid == 0:
                continue
            row, col = index_to_cell(index, map_width)
            local = gid - find_firstgid(gid, firstgids)
            surface.blit(tiles[local], (col * SCALE * TILE, row * SCALE * TILE))

    return surface

if __name__ == "__main__":
    # test code here: only runs when you run tilemap.py directly
    assert index_to_cell(5, 4) == (1, 1)
    print("step 1 OK")