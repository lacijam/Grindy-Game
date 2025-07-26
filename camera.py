import pygame
import random

class Camera:
    def __init__(self, offset, viewport_width, viewport_height):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

        self.offset = pygame.Vector2(offset)
        self._base_offset = pygame.Vector2(0, 0)

        self.shake_timer = 0.0
        self.shake_magnitude = 0.0
        self.shake_duration = 0.0

    def apply(self, target):
        if isinstance(target, pygame.Rect):
            return target.move(self.offset)
        elif isinstance(target, (pygame.Vector2, tuple)):
            return pygame.Vector2(target) + self.offset
        return target

    def reverse(self, pos):
        return (pos[0] + self.offset.x, pos[1] + self.offset.y)

    def shake(self, magnitude=8, duration=0.25):
        self.shake_magnitude = magnitude
        self.shake_timer = duration
        self.shake_duration = duration

    def center_on(self, rect):
        self._base_offset.x = -rect.centerx + self.viewport_width // 2
        self._base_offset.y = -rect.centery + self.viewport_height // 2

    def _apply_shake(self, dt):
        if self.shake_timer > 0:
            self.shake_timer -= dt
            t = self.shake_timer / self.shake_duration
            eased = self.shake_magnitude * (t ** 2)
            shake = pygame.Vector2(
                random.uniform(-eased, eased),
                random.uniform(-eased, eased)
            )
            self.offset = self._base_offset + shake
        else:
            self.offset = self._base_offset

    def update(self, dt, player_rect=None):
        self.center_on(player_rect)

        self._apply_shake(dt)