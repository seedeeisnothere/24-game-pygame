# Screen and timing
SCREEN_HEIGHT = 800
SCREEN_WIDTH = 1280
FPS = 60

# Player movement and hitbox
WALK_SPEED = 5
WALK_FRAME_MS = 60
HITBOX_WIDTH = 40
HITBOX_HEIGHT = 36

# Font and sound effects
FONT_PATH = "assets/fonts/BoldPixels.ttf"
HOVER_SFX_PATH = "assets/sfx/Hover.wav"
SELECT_SFX_PATH = "assets/sfx/Select.wav"
PICKUP_SFX_PATH = "assets/sfx/Pickup.wav"
EXPLOSION_SFX_PATH = "assets/sfx/Explosion.wav"
SHOOT_SFX_PATH = "assets/sfx/Shoot.wav"
HIT_SFX_PATH = "assets/sfx/Hit.wav"
DEATH_SFX_PATH = "assets/sfx/Death.wav"
POWERUP_SFX_PATH = "assets/sfx/PowerUp.wav"
WALK_GRASS_SFX_PATHS = ["assets/sfx/Walk_Grass1.wav", "assets/sfx/Walk_Grass2.wav"]
WALK_GRASS_VOLUME = 0.3
WALK_GRASS_DELAY_MS = 40

# Title screen and buttons
TITLE_FONT_SIZE = 128
BUTTON_FONT_SIZE = 48
TEXT_COLOR = "#FFFFFF"
TITLE_BG_COLOR = "#080A12"
BUTTON_COLOR = "#2F5D8A"
BUTTON_HOVER_COLOR = "#5A82AA"
BUTTON_PRESSED_COLOR = "#28415A"
BUTTON_FILL_COLOR = "#070A12"
BUTTON_BORDER_WIDTH = 7
BUTTON_RADIUS = 17
BUTTON_WIDTH = 448
BUTTON_HEIGHT = 96
BUTTON_GAP = 24
HOME_BUTTON_RADIUS = BUTTON_HEIGHT // 2
HOME_ICON_SIZE = 44

# Longest frame time allowed (seconds), so lag spikes don't jump
MAX_DT = 0.05

# Scene-change curtain
CURTAIN_COLOR = "#000000"
CURTAIN_SLIDE_TIME = 0.4
CURTAIN_HOLD_TIME = 0.5

# Audio
DEFAULT_SFX_VOLUME = 0.7
DEFAULT_BGM_VOLUME = 0.3

# Background music, one file per scene/mood (all CC0 from OpenGameArt)
MUSIC_FADE_MS = 600
# Scales all music down so it sits behind the sound effects.
# 0.4 is about 8 dB quieter; lower = quieter music.
MUSIC_MASTER = 0.4
MUSIC_PATHS = {
    "title": "assets/music/title.flac",   # volume-boosted (the original .ogg was very quiet)
    "map1": "assets/music/map1.mp3",
    "map2": "assets/music/map2.flac",     # volume-boosted (the original .ogg was very quiet)
    "battle": "assets/music/battle.ogg",
    "boss": "assets/music/boss.ogg",
    "gameover": "assets/music/gameover.ogg",
    "ending": "assets/music/ending.mp3",
}
# Per-track volume (0-1) so every song plays at the same loudness (~-18 LUFS).
# Measured with ffmpeg's ebur128; loud tracks are turned down here.
MUSIC_GAIN = {
    "title": 1.0,
    "map1": 0.79,      # -15.9 LUFS
    "map2": 1.0,
    "battle": 0.66,    # -14.4 LUFS
    "boss": 0.32,      # -8.1 LUFS
    "gameover": 1.0,   # -17.9 LUFS
    "ending": 0.45,    # -11.1 LUFS
}

# Slide-in panels and small text
PANEL_COLOR = "#1E2438"
PANEL_SLIDE_TIME = 0.35
PANEL_MARGIN = 80
SMALL_FONT_SIZE = 32

# Credits
CREDITS_FONT_SIZE = 24
CREDITS_FIRST_Y = 200
CREDITS_LINE_HEIGHT = 40
CREDITS_LINES = [
    "Player: Among Us (Innersloth)",
    "NPCs: Tiny Neighbours by vryell",
    "Tiles: Valley of Ruin by kinodev",
    "Tiles: Spring Forest by Seliel",
    "Font: BoldPixels by Yuki",
    "SFX: bfxr, Pixabay",
    "Music: OpenGameArt.org",
]

# Volume sliders
SLIDER_FIRST_Y = 260
SLIDER_SPACING = 130
FULLSCREEN_BUTTON_Y = 510
SLIDER_WIDTH = 400
SLIDER_TRACK_HEIGHT = 12
SLIDER_HANDLE_WIDTH = 20
SLIDER_HANDLE_HEIGHT = 40
SLIDER_LABEL_GAP = 32
SLIDER_PERCENT_GAP = 24
SLIDER_TRACK_COLOR = "#3C4664"
SLIDER_FILL_COLOR = "#5A82AA"
SLIDER_HANDLE_COLOR = "#FFFFFF"

# Twinkling stars on the title screen
STAR_MIN_DISTANCE = 105
STAR_MAX_TRIES = 3000
STAR_MARGIN = 10
STAR_CLEARANCE = 10
STAR_RADIUS = 5
STAR_COLOR = "#D9D9D9"
STAR_BRIGHTNESS_MIN = 0.7
STAR_LEVELS = [1.0, 0.65, 0.35, 0.65]
STAR_STEP_TIME = 0.12
STAR_WAIT_MIN = 4.0
STAR_WAIT_MAX = 15.0

# Planet on the title screen (centered on the bottom-right corner)
PLANET_CENTER = (SCREEN_WIDTH, SCREEN_HEIGHT)
PLANET_IMAGE_PATH = "assets/sprites/planet.png"
PLANET_SCALE = 21
PLANET_RADIUS = 630
PLANET_INTRO_TIME = 1.0
PLANET_EASE = 2
PLANET_START_OFFSET = 620
PLANET_BOB_AMPLITUDE = 10
PLANET_BOB_PERIOD = 4.0

# Item icons and coin display
POTION_ICON_PATH = "assets/item_assets/Healing_Potion.png"
SKIP_ICON_PATH = "assets/item_assets/Skip_Ticket.png"
COIN_ICON_PATH = "assets/item_assets/Coin.png"
COIN_ICON_HEIGHT = 40
COIN_GAP = 10
