import pygame
import constants as c
from primitives import Pose
import time
import math

class BossHealthBar:
    PLAYER_BAR_OFFSET = (55, 16)
    PLAYER_BAR_Y = 20

    BOSS_BACKGROUND_Y_OFFSET = 175
    BOSS_HEAD_BAR_X_OFFSET = 89
    BOSS_HEAD_BAR_Y_OFFSET = -48 #127

    HAND_BAR_LEFT_X_OFFSET = 213
    HAND_BAR_RIGHT_X_OFFSET = 213
    HAND_BAR_Y_OFFSET = 86

    HANDS_ANIMATION_SPEED = 10
    HANDS_ANIMATION_AMPLITUDE = 3

    def __init__(self, boss):
        self.boss = boss
        self.load_images()
        self.visible = False

    def load_images(self):
        self.background = pygame.image.load("assets/images/boss_bar.png")
        self.head_bar = pygame.image.load("assets/images/boss_hp.png")
        self.head_bar_blink = pygame.image.load("assets/images/boss_hp_blink.png")
        self.head_bar.set_colorkey((255, 0, 255))
        self.hand_bar_left = pygame.image.load("assets/images/boss_hand_hp_left.png")
        self.hand_bar_left_blink = pygame.image.load("assets/images/boss_hand_hp_left_blink.png")
        self.hand_bar_left_blink.set_colorkey((255, 0, 255))
        self.hand_bar_left.set_colorkey((255, 255, 255))
        self.hand_bar_right = pygame.transform.flip(self.hand_bar_left, True, False)
        self.hand_bar_right_blink = pygame.transform.flip(self.hand_bar_left_blink, True, False)
        self.hands = pygame.image.load("assets/images/boss bar hands.png")
        self.player_bar = pygame.image.load("assets/images/hp_bar_front.png")
        self.player_bar_back = pygame.image.load("assets/images/hp_bar_back.png")
        self.player_bar_front_low = pygame.image.load("assets/images/hp_bar_front_low.png")
        self.player_bar.set_colorkey((255, 0, 255))

    def update(self, dt, events):
        pass

    def draw(self, surface, offset=(0, 0)):
        self.draw_player_health(surface)
        if self.visible:
            self.draw_boss_health(surface)
            self.draw_hand_health(surface)
            self.draw_animated_hands(surface)

    def draw_player_health(self, surface):
        x, y = c.WINDOW_WIDTH // 2 - self.player_bar_back.get_width() // 2, self.PLAYER_BAR_Y
        surface.blit(self.player_bar_back, (x, y))
        x += self.PLAYER_BAR_OFFSET[0]
        y += self.PLAYER_BAR_OFFSET[1]
        w = int(self.player_bar.get_width() * self.boss.frame.player.health / 100)
        h = self.player_bar.get_height()
        if self.boss.frame.player.health > 40:
            surface.blit(self.player_bar, (x, y), (0, 0, w, h))
        elif w > 0:
            surface.blit(self.player_bar_front_low, (x, y), (0, 0, w, h))

    def draw_boss_health(self, surface):
        bx = c.WINDOW_WIDTH // 2 - self.background.get_width() // 2
        by = c.WINDOW_HEIGHT - self.BOSS_BACKGROUND_Y_OFFSET
        surface.blit(self.background, (bx, by))
        self.draw_health_bar(
            surface,
            self.head_bar,
            self.head_bar_blink,
            self.boss.health,
            self.boss.max_health,
            self.boss.health_recently_lost,
            bx + self.BOSS_HEAD_BAR_X_OFFSET,
            by - self.BOSS_HEAD_BAR_Y_OFFSET
        )

    def draw_hand_health(self, surface):
        left_x = c.WINDOW_WIDTH // 2 - self.hand_bar_left.get_width() // 2 - self.HAND_BAR_LEFT_X_OFFSET
        right_x = c.WINDOW_WIDTH // 2 - self.hand_bar_left.get_width() // 2 + self.HAND_BAR_RIGHT_X_OFFSET
        y = c.WINDOW_HEIGHT - self.HAND_BAR_Y_OFFSET
        self.draw_health_bar(
            surface,
            self.hand_bar_left,
            self.hand_bar_left_blink,
            self.boss.hands[1].health,
            self.boss.hands[1].max_health,
            self.boss.hands[1].health_recently_lost,
            left_x,
            y
        )
        self.draw_health_bar(
            surface,
            self.hand_bar_right,
            self.hand_bar_right_blink,
            self.boss.hands[0].health,
            self.boss.hands[0].max_health,
            self.boss.hands[0].health_recently_lost,
            right_x,
            y
        )

    def draw_health_bar(self, surface, bar_image, blink_image, current_health, max_health, recently_lost_health, x, y):
        w = int(bar_image.get_width() * current_health / max_health)
        h = bar_image.get_height()
        if w > 0:
            surface.blit(bar_image, (x, y), (0, 0, w, h))
            if recently_lost_health:
                sliver = blink_image.subsurface((w, 0, blink_image.get_width() * recently_lost_health / max_health, h)).copy()
                sliver.set_colorkey((255, 0, 255))
                surface.blit(sliver, (x + w, y))

    def draw_animated_hands(self, surface):
        bx = c.WINDOW_WIDTH // 2 - self.background.get_width() // 2
        by = c.WINDOW_HEIGHT - self.BOSS_BACKGROUND_Y_OFFSET
        surface.blit(self.hands, (bx + 3, by + self.HANDS_ANIMATION_AMPLITUDE * math.sin(time.time() * self.HANDS_ANIMATION_SPEED)))
