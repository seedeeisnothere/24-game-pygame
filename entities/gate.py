# A gate made of tiles that blocks the player until it is opened.
class Gate:
    def __init__(self, tiles, rects):
        self.tiles = tiles      # list of (tile image, (x, y))
        self.rects = rects      # solid rects used for collision
        self.open = False

    # True if the closed gate is in the way of this hitbox.
    def blocks(self, hitbox):
        if self.open:
            return False
        return any(hitbox.colliderect(rect) for rect in self.rects)

    # Draw the gate tiles (nothing once it's open).
    def draw(self, screen, cam_x, cam_y):
        if self.open:
            return
        for tile, position in self.tiles:
            screen.blit(tile, (position[0] - cam_x, position[1] - cam_y))
