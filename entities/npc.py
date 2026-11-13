import pygame

FRAME = 16                # NPC sprite sheets are a grid of 16x16 frames
SHEET_SCALE = 5           # 16 px frame -> 80 px on screen (about player height)
IDLE_FRAMES = 4           # first 4 columns of a row are the idle animation
IDLE_FRAME_TIME = 0.25    # seconds per idle frame
FACING_DOWN_ROW = 1       # row 0 is the "IDLE / WALK" header
SHADOW_SIZE = (64, 18)    # soft oval drawn under the NPC's feet
SHADOW_ALPHA = 90
SHADOW_RAISE = 1          # shadow center sits this many px above the feet


# A see-through dark oval, made once and shared by every NPC.
_shadow = None


def get_shadow():
    global _shadow
    if _shadow is None:
        _shadow = pygame.Surface(SHADOW_SIZE, pygame.SRCALPHA)
        pygame.draw.ellipse(_shadow, (0, 0, 0, SHADOW_ALPHA), _shadow.get_rect())
    return _shadow


# Cut the facing-down idle frames out of an NPC sprite sheet.
def load_idle_frames(path):
    sheet = pygame.image.load(path).convert_alpha()
    size = (FRAME * SHEET_SCALE, FRAME * SHEET_SCALE)
    frames = []
    for col in range(IDLE_FRAMES):
        frame = sheet.subsurface((col * FRAME, FACING_DOWN_ROW * FRAME, FRAME, FRAME))
        frames.append(pygame.transform.scale(frame, size))
    return frames


# A character in the overworld the player can talk to (or shop with).
# sheet=True means image_path is a sprite sheet (like NPC_5.png) and the NPC
# plays its idle animation; otherwise image_path is one still image.
class NPC:
    def __init__(self, name, x, y, image_path, dialogue_id, portrait_path=None,
                 shop_id=None, sheet=False, on_minimap=False):
        self.name = name
        self.dialogue_id = dialogue_id
        self.shop_id = shop_id
        # True = shown on the minimap as a blue diamond
        self.on_minimap = on_minimap

        if sheet:
            self.frames = load_idle_frames(image_path)
        else:
            self.frames = [pygame.transform.scale(
                pygame.image.load(image_path).convert_alpha(), (64, 87))]
        self.frame_index = 0
        self.timer = 0.0
        self.image = self.frames[0]
        self.rect = self.image.get_rect(topleft=(x, y))

        # Feet hitbox like the player's; used for collision and talk range
        self.hitbox = pygame.Rect(0, 0, 40, 36)
        self.hitbox.midbottom = self.rect.midbottom

        self.portrait = None
        if portrait_path:
            self.portrait = pygame.image.load(portrait_path).convert_alpha()

    # Move the NPC so its feet (bottom middle) are at `feet`.
    def place(self, feet):
        self.rect.midbottom = feet
        self.hitbox.midbottom = feet

    # Step through the idle animation (does nothing for still images).
    def update(self, dt):
        if len(self.frames) < 2:
            return
        self.timer += dt
        if self.timer >= IDLE_FRAME_TIME:
            self.timer -= IDLE_FRAME_TIME
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.image = self.frames[self.frame_index]

    # True if the player is within `reach` pixels of the NPC's feet.
    def can_interact(self, player_hitbox, reach=24):
        return self.hitbox.inflate(reach * 2, reach * 2).colliderect(player_hitbox)

    # True if the mouse is over the NPC.
    def is_clicked(self, mouse_pos, cam_x, cam_y):
        # Convert screen mouse position to world position
        return self.rect.collidepoint(mouse_pos[0] + cam_x, mouse_pos[1] + cam_y)

    def draw(self, screen, cam_x, cam_y):
        # Shadow first, so the NPC is drawn standing on it
        shadow = get_shadow()
        feet = (self.rect.centerx - cam_x, self.rect.bottom - SHADOW_RAISE - cam_y)
        screen.blit(shadow, shadow.get_rect(center=feet))
        screen.blit(self.image, (self.rect.x - cam_x, self.rect.y - cam_y))
