import json
import os
import pygame

PLAYER_NAME = "Hero"


def load_font(path, size):
    if os.path.exists(path):
        return pygame.font.Font(path, size)
    print(f"[warn] font not found: {path}")
    return pygame.font.SysFont("arial", size)

class DialogueSystem:
    def __init__(self, json_path, screen_size):
        with open(json_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.screen_w, self.screen_h = screen_size
        self.active = False
        self.lines = []
        self.index = 0
        self.npc = None

        # ฟอนต์ไทย: pygame font default ไม่รองรับภาษาไทย ต้องใช้ไฟล์ .ttf
        self.font = load_font("assets/fonts/BoldPixels.ttf", 28)
        self.name_font = load_font("assets/fonts/BoldPixels.ttf", 30)

        self.box_rect = pygame.Rect(40, self.screen_h - 220, self.screen_w - 80, 190)

    def start(self, npc):
        lines = self.data.get(npc.dialogue_id)
        if not lines:
            return
        self.npc = npc
        self.lines = lines
        self.index = 0
        self.active = True

    def advance(self):
        self.index += 1
        if self.index >= len(self.lines):
            self.active = False
            self.npc = None

    def handle_events(self, events):
        if not self.active:
            return
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.advance()
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
                self.advance()

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

    def _draw_name_tag(self, screen, name, topleft=None, topright=None):
        label = self.name_font.render(name, True, (255, 255, 255))
        tag = pygame.Rect(0, 0, label.get_width() + 32, label.get_height() + 12)
        if topleft:
            tag.bottomleft = topleft
        else:
            tag.bottomright = topright
        pygame.draw.rect(screen, (40, 40, 70), tag, border_radius=8)
        pygame.draw.rect(screen, (230, 230, 255), tag, 2, border_radius=8)
        screen.blit(label, (tag.x + 16, tag.y + 6))

    def draw(self, screen):
        if not self.active:
            return

        line = self.lines[self.index]

        # กล่องข้อความ
        pygame.draw.rect(screen, (20, 20, 40), self.box_rect, border_radius=12)
        pygame.draw.rect(screen, (230, 230, 255), self.box_rect, 3, border_radius=12)

        # ชื่อผู้เล่น: บนซ้ายของกล่อง
        self._draw_name_tag(screen, PLAYER_NAME, topleft=self.box_rect.topleft)

        # NPC: บนขวา (ชื่อ + portrait ถ้ามี)
        self._draw_name_tag(screen, self.npc.name, topright=self.box_rect.topright)
        if self.npc.portrait:
            p = self.npc.portrait
            screen.blit(p, p.get_rect(bottomright=(self.box_rect.right - 10,
                                                    self.box_rect.top - 50)))

        # ข้อความ
        y = self.box_rect.y + 24
        for row in self._wrap(line["text"], self.box_rect.width - 60):
            screen.blit(self.font.render(row, True, (255, 255, 255)), (self.box_rect.x + 30, y))
            y += 36

        # ตัวบอกว่าคลิกต่อได้
        hint = self.font.render("v Click or press E to continue", True, (180, 180, 220))
        screen.blit(hint, (self.box_rect.right - hint.get_width() - 24,
                           self.box_rect.bottom - 40))