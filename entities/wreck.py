import random
import pygame

# Wreck look
WRECK_IMAGE_PATH = "assets/sprites/spaceship/wreck.png"
FIXED_IMAGE_PATH = "assets/sprites/spaceship/fixed.png"   # repaired, standing up
WRECK_SCALE = 6                     # much bigger than the player
OUTLINE_COLOR = (52, 34, 30, 170)   # dark, slightly see-through brown
OUTLINE_WIDTH = 2                   # in screen pixels, after scaling
TINT = (232, 214, 198)              # multiplied in to look dirty/warm
SHADOW_COLOR = (40, 24, 20, 90)

# Smoke
SMOKE_INTERVAL = 0.35               # seconds between new puffs
SMOKE_LIFE = 2.2                    # seconds a puff lasts
SMOKE_RISE = 40                     # pixels per second


# Draw an outline around the outside edge of the image only
# (holes inside the ship do not get an outline).
def add_outline(image, width=OUTLINE_WIDTH):
    w, h = image.get_size()
    # Add empty space around the image so the outline fits
    padded = pygame.Surface((w + width * 2, h + width * 2), pygame.SRCALPHA)
    padded.blit(image, (width, width))

    shape = pygame.mask.from_surface(padded)
    empty = shape.copy()
    empty.invert()
    # Empty pixels connected to the corner = the real outside area
    outside = empty.connected_component((0, 0))

    # "Grow" the shape by stamping it at every offset inside a circle
    ring = pygame.mask.Mask(padded.get_size())
    for dx in range(-width, width + 1):
        for dy in range(-width, width + 1):
            if dx * dx + dy * dy <= width * width:
                ring.draw(shape, (dx, dy))
    # Keep only the part of the grown shape that lies outside
    ring = ring.overlap_mask(outside, (0, 0))

    outlined = ring.to_surface(setcolor=OUTLINE_COLOR, unsetcolor=(0, 0, 0, 0))
    outlined.blit(padded, (0, 0))
    return outlined


# The crashed spaceship at the player's start: solid, with rising smoke.
class Wreck:
    # (ground_x, ground_y) is the bottom-center of the ship on the ground.
    def __init__(self, ground_x, ground_y):
        image = pygame.image.load(WRECK_IMAGE_PATH).convert_alpha()
        size = (image.get_width() * WRECK_SCALE, image.get_height() * WRECK_SCALE)
        image = pygame.transform.scale(image, size)
        image.fill(TINT, special_flags=pygame.BLEND_RGB_MULT)
        self.image = add_outline(image)

        # Find the area with real pixels (the sprite has empty space top/bottom)
        parts = pygame.mask.from_surface(self.image).get_bounding_rects()
        local = parts[0].unionall(parts[1:])
        self.rect = self.image.get_rect(
            topleft=(ground_x - local.centerx, ground_y - local.bottom))
        body = local.move(self.rect.topleft)
        self.body = body
        # Only the bottom half is solid, so the player can walk behind the top
        self.hitbox = pygame.Rect(body.x + 12, body.centery,
                                  body.width - 24, body.bottom - body.centery)

        # Oval shadow under the ship so it looks like it sits on the ground
        self.shadow = pygame.Surface((round(body.width * 0.9), 44), pygame.SRCALPHA)
        pygame.draw.ellipse(self.shadow, SHADOW_COLOR, self.shadow.get_rect())
        self.shadow_rect = self.shadow.get_rect(center=(body.centerx, body.bottom - 14))

        self.smoke = []         # each puff is [x, y, age]
        self.smoke_timer = 0.0
        self.fixed = False

    # Swap to the repaired ship (ending cutscene): same spot, no more smoke.
    # The hitbox stays the same, so nothing on the map moves.
    def fix(self):
        image = pygame.image.load(FIXED_IMAGE_PATH).convert_alpha()
        size = (image.get_width() * WRECK_SCALE, image.get_height() * WRECK_SCALE)
        self.image = pygame.transform.scale(image, size)
        # Stand the ship's lowest pixel on the same ground point as the wreck
        local = self.image.get_bounding_rect()
        ground_x, ground_y = self.body.centerx, self.body.bottom
        self.rect = self.image.get_rect(
            topleft=(ground_x - local.centerx, ground_y - local.bottom))
        self.smoke = []
        self.fixed = True

    # Y value used to sort drawing order (things lower on screen draw on top).
    @property
    def sort_y(self):
        return self.body.bottom

    # Add new smoke puffs on a timer and move/age the existing ones.
    def update(self, dt):
        self.smoke_timer -= dt
        if self.smoke_timer <= 0 and not self.fixed:
            self.smoke_timer = SMOKE_INTERVAL
            x = random.uniform(self.body.centerx - 20, self.body.centerx + 30)
            self.smoke.append([x, self.body.centery, 0.0])
        for puff in self.smoke:
            puff[1] -= SMOKE_RISE * dt   # rise up
            puff[0] += 6 * dt            # drift slightly right
            puff[2] += dt                # get older
        self.smoke = [puff for puff in self.smoke if puff[2] < SMOKE_LIFE]

    def draw(self, screen, cam_x, cam_y):
        screen.blit(self.shadow, (self.shadow_rect.x - cam_x, self.shadow_rect.y - cam_y))
        screen.blit(self.image, (self.rect.x - cam_x, self.rect.y - cam_y))

    # Draw smoke puffs that grow bigger and fade out as they age.
    def draw_smoke(self, screen, cam_x, cam_y):
        for x, y, age in self.smoke:
            life = age / SMOKE_LIFE      # 0.0 = new, 1.0 = about to vanish
            radius = round(8 + 14 * life)
            alpha = round(150 * (1 - life))
            puff = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(puff, (90, 90, 95, alpha), (radius, radius), radius)
            screen.blit(puff, (x - radius - cam_x, y - radius - cam_y))
