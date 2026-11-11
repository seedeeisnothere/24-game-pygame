# Screen and timing
SCREEN_HEIGHT = 800
SCREEN_WIDTH = 1280
FPS = 60

# Player movement and hitbox
WALK_SPEED = 4
WALK_FRAME_MS = 75
HITBOX_WIDTH = 40
HITBOX_HEIGHT = 36

# Font and sound effects
FONT_PATH = "assets/fonts/BoldPixels.ttf"
HOVER_SFX_PATH = "assets/sfx/Hover.wav"
SELECT_SFX_PATH = "assets/sfx/Select.wav"
WALK_GRASS_SFX_PATHS = ["assets/sfx/Walk_grass1.wav", "assets/sfx/Walk_Grass2.wav"]
WALK_GRASS_VOLUME = 0.3
WALK_GRASS_DELAY_MS = 135

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
DEFAULT_BGM_VOLUME = 0.7

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
    "Art: Sprout Lands by Cup Nooble",
    "Font: BoldPixels by Yuki",
]

# Volume sliders
SLIDER_FIRST_Y = 320
SLIDER_SPACING = 140
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

# Battle dodge attacks (times in seconds)
ATTACK_WAIT = (2.5, 5.0)        # min/max wait between waves
WAVE_SIZES = (1, 1, 2)          # picked at random, so 1 is twice as likely
ATTACK_GAP = (1.2, 2.0)         # min/max gap between attacks in a wave
MAX_ATTACKS = 2
DODGE_TIME = 1.8                # time to press the key
DODGE_KEYS = "WASD"

# Item icons and coin display
POTION_ICON_PATH = "assets/item_assets/Healing_Potion.png"
COIN_ICON_PATH = "assets/item_assets/Coin.png"
COIN_ICON_HEIGHT = 40
COIN_GAP = 10
