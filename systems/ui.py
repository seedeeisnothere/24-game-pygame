import pygame
from settings import *


# A rectangular clickable button with a text label.
class Button:
    def __init__(self, text, center, font, width=BUTTON_WIDTH):
        self.rect = pygame.Rect(0, 0, width, BUTTON_HEIGHT)
        self.rect.center = center
        self.font = font
        self.set_text(text)
        self.hovered = False
        self.pressed = False

    # Change the label (re-rendered only when the text really changes).
    def set_text(self, text):
        if getattr(self, "text", None) == text:
            return
        self.text = text
        self.label = self.font.render(text, False, TEXT_COLOR)
        self.label_rect = self.label.get_rect(center=self.rect.center)

    # Update hover state. Returns True only on the frame the mouse enters.
    def update(self, mouse_pos):
        was_hovered = self.hovered
        self.hovered = self.rect.collidepoint(mouse_pos)
        return self.hovered and not was_hovered

    # Returns True when a full click (press + release on the button) happens.
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_pressed = self.pressed
            self.pressed = False
            return was_pressed and self.rect.collidepoint(event.pos)
        return False

    # Draw the button, changing colours when hovered or pressed.
    def draw(self, screen):
        fill_color = BUTTON_FILL_COLOR
        border_color = BUTTON_COLOR
        if self.pressed and self.hovered:
            fill_color = BUTTON_PRESSED_COLOR
            border_color = BUTTON_HOVER_COLOR
        elif self.hovered:
            border_color = BUTTON_HOVER_COLOR
        pygame.draw.rect(screen, fill_color, self.rect, border_radius=BUTTON_RADIUS)
        pygame.draw.rect(screen, border_color, self.rect,
                         width=BUTTON_BORDER_WIDTH, border_radius=BUTTON_RADIUS)
        screen.blit(self.label, self.label_rect)


# A round button with a small house icon (goes back to the title screen).
class HomeButton:
    def __init__(self, center):
        self.center = center
        self.hovered = False
        self.pressed = False

    # The button is a circle, so check distance from the center.
    def contains(self, point):
        return pygame.math.Vector2(self.center).distance_to(point) <= HOME_BUTTON_RADIUS

    # Update hover state. Returns True only on the frame the mouse enters.
    def update(self, mouse_pos):
        was_hovered = self.hovered
        self.hovered = self.contains(mouse_pos)
        return self.hovered and not was_hovered

    # Returns True when a full click (press + release on the button) happens.
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.contains(event.pos):
                self.pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_pressed = self.pressed
            self.pressed = False
            return was_pressed and self.contains(event.pos)
        return False

    # Draw the circle, then a house made of a triangle roof, body and door.
    def draw(self, screen):
        fill_color = BUTTON_FILL_COLOR
        border_color = BUTTON_COLOR
        if self.pressed and self.hovered:
            fill_color = BUTTON_PRESSED_COLOR
            border_color = BUTTON_HOVER_COLOR
        elif self.hovered:
            border_color = BUTTON_HOVER_COLOR
        pygame.draw.circle(screen, fill_color, self.center, HOME_BUTTON_RADIUS)
        pygame.draw.circle(screen, border_color, self.center, HOME_BUTTON_RADIUS, BUTTON_BORDER_WIDTH)
        center_x, center_y = self.center
        half = HOME_ICON_SIZE // 2
        # Roof: triangle sitting on the center line
        roof = [(center_x - half, center_y), (center_x, center_y - half), (center_x + half, center_y)]
        pygame.draw.polygon(screen, TEXT_COLOR, roof)
        # Body: rectangle hanging below the roof
        body = pygame.Rect(0, 0, HOME_ICON_SIZE * 3 // 4, HOME_ICON_SIZE // 2)
        body.midtop = (center_x, center_y)
        pygame.draw.rect(screen, TEXT_COLOR, body)
        # Door: small rectangle cut out using the fill colour
        door = pygame.Rect(0, 0, HOME_ICON_SIZE // 4, HOME_ICON_SIZE // 3)
        door.midbottom = body.midbottom
        pygame.draw.rect(screen, fill_color, door)


# A horizontal slider for a value between 0 and 1 (used for volume).
class Slider:
    def __init__(self, label, left, centery, value, font):
        self.font = font
        self.label = font.render(label, False, TEXT_COLOR)
        self.track = pygame.Rect(left, 0, SLIDER_WIDTH, SLIDER_TRACK_HEIGHT)
        self.track.centery = centery
        self.label_rect = self.label.get_rect(bottomleft=(left, centery - SLIDER_LABEL_GAP))
        self.handle = pygame.Rect(0, 0, SLIDER_HANDLE_WIDTH, SLIDER_HANDLE_HEIGHT)
        self.handle.centery = centery
        # Bigger click area than the thin track, so it's easier to grab
        self.hit_rect = self.track.inflate(SLIDER_HANDLE_WIDTH, SLIDER_HANDLE_HEIGHT)
        self.dragging = False
        self.set_value(value)

    # Clamp value to 0..1, move the handle and update the % text.
    def set_value(self, value):
        self.value = max(0, min(value, 1))
        self.handle.centerx = self.track.left + round(self.value * self.track.width)
        self.percent = self.font.render(f"{round(self.value * 100)}%", False, TEXT_COLOR)
        self.percent_rect = self.percent.get_rect(
            midleft=(self.track.right + SLIDER_PERCENT_GAP, self.track.centery))

    # Convert mouse x to a 0..1 value along the track (not clamped).
    def value_from_mouse(self, mouse_x):
        return (mouse_x - self.track.left) / self.track.width

    # Drag to change the value. Returns True when the mouse is released.
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hit_rect.collidepoint(event.pos):
                self.dragging = True
                self.set_value(self.value_from_mouse(event.pos[0]))
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            self.set_value(self.value_from_mouse(event.pos[0]))
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            was_dragging = self.dragging
            self.dragging = False
            return was_dragging
        return False

    # Draw label, track, filled part (left of handle), handle and %.
    def draw(self, screen):
        screen.blit(self.label, self.label_rect)
        pygame.draw.rect(screen, SLIDER_TRACK_COLOR, self.track)
        filled = pygame.Rect(self.track.left, self.track.top,
                             self.handle.centerx - self.track.left, self.track.height)
        pygame.draw.rect(screen, SLIDER_FILL_COLOR, filled)
        pygame.draw.rect(screen, SLIDER_HANDLE_COLOR, self.handle)
        screen.blit(self.percent, self.percent_rect)
