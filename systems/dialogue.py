import json
import os
import pygame

PLAYER_NAME = "John"


# Load a .ttf font, or fall back to Arial if the file is missing.
def load_font(path, size):
    if os.path.exists(path):
        return pygame.font.Font(path, size)
    print(f"[warn] font not found: {path}")
    return pygame.font.SysFont("arial", size)


# Shows NPC conversations in a text box at the bottom of the screen.
class DialogueSystem:
    def __init__(self, json_path, screen_size):
        # data maps a dialogue id to a list of lines like {"text": ...}
        with open(json_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.screen_w, self.screen_h = screen_size
        self.active = False
        self.lines = []
        self.index = 0
        self.npc = None
        self.on_finish = None
        # A line can have "cue": "<name>" to play something (like a camera pan)
        # before it shows. cue_handler(name, done) is set by the scene; while it
        # plays the box is hidden and input is ignored, until done() is called.
        self.cue_handler = None
        self.paused = False
        # Called each time the player moves to the next line (set by the scene,
        # e.g. to play a click sound).
        self.on_advance = None

        # A custom .ttf is needed; the default pygame font can't show Thai
        self.font = load_font("assets/fonts/BoldPixels.ttf", 28)
        self.name_font = load_font("assets/fonts/BoldPixels.ttf", 30)

        # Text box: 40px side margin, 190px tall, 30px above the bottom
        self.box_rect = pygame.Rect(40, self.screen_h - 220, self.screen_w - 80, 190)

    # Start talking to an NPC. on_finish runs after the last line.
    # dialogue_id overrides the NPC's usual one (e.g. quest-dependent lines).
    def start(self, npc, on_finish=None, dialogue_id=None):
        lines = self.data.get(dialogue_id or npc.dialogue_id)
        if not lines:
            # No dialogue for this NPC, so finish straight away
            if on_finish:
                on_finish()
            return
        self.npc = npc
        self.on_finish = on_finish
        self.lines = lines
        self.index = 0
        self.active = True
        self._play_cue()

    # If the current line has a cue, pause and let the scene play it.
    def _play_cue(self):
        cue = self.lines[self.index].get("cue")
        if not cue or not self.cue_handler:
            return
        self.paused = True
        npc = self.npc

        def done():
            # Ignore if the dialogue was closed or restarted meanwhile
            if self.active and self.npc is npc:
                self.paused = False

        self.cue_handler(cue, done)

    # Close the dialogue early without calling on_finish.
    def cancel(self):
        self.active = False
        self.paused = False
        self.npc = None
        self.on_finish = None

    # Go to the next line; close and run the callback after the last one.
    def advance(self):
        self.index += 1
        if self.index < len(self.lines):
            self._play_cue()
        if self.index >= len(self.lines):
            self.active = False
            self.npc = None
            # Clear on_finish before calling it, so it only runs once
            callback, self.on_finish = self.on_finish, None
            if callback:
                callback()

    # Left click, E, Space or Enter moves to the next line.
    def handle_events(self, events):
        if not self.active or self.paused:
            return
        for event in events:
            pressed = ((event.type == pygame.MOUSEBUTTONDOWN and event.button == 1)
                       or (event.type == pygame.KEYDOWN
                           and event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN)))
            if pressed:
                if self.on_advance:
                    self.on_advance()
                self.advance()

    # Split text into lines that fit inside max_width pixels (word wrap).
    def _wrap(self, text, max_width):
        words = text.split(" ")
        lines, current = [], ""
        for word in words:
            test = word if not current else current + " " + word
            if self.font.size(test)[0] > max_width:
                lines.append(current)
                current = word
            else:
                current = test
        lines.append(current)
        return lines

    # Draw a name label sitting on top of the box's left or right corner.
    def _draw_name_tag(self, screen, name, topleft=None, topright=None):
        label = self.name_font.render(name, True, (255, 255, 255))
        # Padding: 16px left/right, 6px top/bottom
        tag = pygame.Rect(0, 0, label.get_width() + 32, label.get_height() + 12)
        if topleft:
            tag.bottomleft = topleft
        else:
            tag.bottomright = topright
        pygame.draw.rect(screen, (40, 40, 70), tag, border_radius=8)
        pygame.draw.rect(screen, (230, 230, 255), tag, 2, border_radius=8)
        screen.blit(label, (tag.x + 16, tag.y + 6))

    # Draw the box, both name tags, the NPC portrait and the current line.
    def draw(self, screen):
        if not self.active or self.paused:
            return

        line = self.lines[self.index]

        # Text box background and border
        pygame.draw.rect(screen, (20, 20, 40), self.box_rect, border_radius=12)
        pygame.draw.rect(screen, (230, 230, 255), self.box_rect, 3, border_radius=12)

        # Only the speaker's name tag shows: player on the left, NPC on the right.
        # Lines without a "speaker" count as the NPC talking.
        if line.get("speaker", "npc") == "player":
            self._draw_name_tag(screen, PLAYER_NAME, topleft=self.box_rect.topleft)
        else:
            self._draw_name_tag(screen, self.npc.name, topright=self.box_rect.topright)
        # NPC portrait above the box, if there is one
        if self.npc.portrait:
            portrait = self.npc.portrait
            screen.blit(portrait, portrait.get_rect(bottomright=(self.box_rect.right - 10,
                                                                  self.box_rect.top - 50)))

        # Wrapped dialogue text, 36px per row
        y = self.box_rect.y + 24
        for row in self._wrap(line["text"], self.box_rect.width - 60):
            screen.blit(self.font.render(row, True, (255, 255, 255)), (self.box_rect.x + 30, y))
            y += 36

        # Hint in the bottom-right corner telling the player how to continue
        hint = self.font.render("v Click or press E to continue", True, (180, 180, 220))
        screen.blit(hint, (self.box_rect.right - hint.get_width() - 24,
                           self.box_rect.bottom - 40))
