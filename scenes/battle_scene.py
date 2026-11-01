import pygame
from settings import *
from scenes.scene import Scene


class BattleScene(Scene):
    """ฉากต่อสู้ชั่วคราว (placeholder) ไว้ทดสอบการสลับฉาก
    Enter = ชนะ (ศัตรูหายไป), Esc = หนี (ศัตรูกลับจุดเริ่ม)"""

    def __init__(self, game, enemy, overworld):
        super().__init__(game)
        self.enemy = enemy
        self.overworld = overworld      # เก็บฉาก overworld เดิมไว้ จะได้กลับมาตำแหน่งเดิม

        big_font = pygame.font.Font(FONT_PATH, BUTTON_FONT_SIZE)
        small_font = pygame.font.Font(FONT_PATH, SMALL_FONT_SIZE)
        self.title = big_font.render(f"VS {enemy.name}", False, TEXT_COLOR)
        self.title_rect = self.title.get_rect(center=(SCREEN_WIDTH // 2, 120))
        self.hint = small_font.render("Enter = win     Esc = run", False, TEXT_COLOR)
        self.hint_rect = self.hint.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100))

        # ขยายรูปศัตรู 3 เท่า (64x87 -> 192x261)
        self.picture = pygame.transform.scale(enemy.sprite.idle_right, (192, 261))
        self.picture_rect = self.picture.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

    def handle_events(self, events):
        for event in events:
            if event.type != pygame.KEYDOWN:
                continue
            if event.key == pygame.K_RETURN:
                self.enemy.defeated = True
                self.back_to_overworld()
            elif event.key == pygame.K_ESCAPE:
                self.enemy.stun()
                self.back_to_overworld()

    def back_to_overworld(self):
        self.game.change_scene(lambda: self.overworld)

    def draw(self, screen):
        screen.fill(TITLE_BG_COLOR)
        screen.blit(self.title, self.title_rect)
        screen.blit(self.picture, self.picture_rect)
        screen.blit(self.hint, self.hint_rect)