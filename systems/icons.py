import pygame


def load_icon(path, height):
    image = pygame.image.load(path).convert_alpha()
    width = round(image.get_width() * height / image.get_height())
    return pygame.transform.scale(image, (width, height))


def dimmed(icon, alpha=90):
    copy = icon.copy()
    copy.set_alpha(alpha)
    return copy