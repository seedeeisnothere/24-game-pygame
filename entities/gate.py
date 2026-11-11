class Gate:
    def __init__(self, tiles, rects):
        self.tiles = tiles
        self.rects = rects
        self.open = False

    def blocks(self, hitbox):
        if self.open:
            return False
        return any(hitbox.colliderect(rect) for rect in self.rects)

    def draw(self, screen, cam_x, cam_y):
        if self.open:
            return
        for tile, position in self.tiles:
            screen.blit(tile, (position[0] - cam_x, position[1] - cam_y))