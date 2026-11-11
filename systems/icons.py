import pygame


# Load an image and scale it to a given height, keeping its aspect ratio.
def load_icon(path, height):
    image = pygame.image.load(path).convert_alpha()
    width = round(image.get_width() * height / image.get_height())
    return pygame.transform.scale(image, (width, height))


# Return a see-through copy of an icon (alpha 0-255), e.g. for "disabled".
def dimmed(icon, alpha=90):
    copy = icon.copy()
    copy.set_alpha(alpha)
    return copy
