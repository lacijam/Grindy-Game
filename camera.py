import pygame
import random

from enum import Enum
class CameraMode(Enum):
    FOLLOW = 0
    PAN = 1
    HOLD = 2

class Camera:
    def __init__(self, offset, viewport_width, viewport_height):
        self.mode = CameraMode.FOLLOW
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

        self.offset = pygame.Vector2(offset)
        self._base_offset = pygame.Vector2(0, 0)

        self.shake_timer = 0.0
        self.shake_magnitude = 0.0
        self.shake_duration = 0.0

        self.pan_target_rect = None
        self.next_pan_target = None
        self.pan_timer = 0
        self.pan_duration = 0
        self.pan_smoothness = 0.2  # between 0–1: how quickly it reaches target

        self.hold_timer = 0
        self.hold_target_rect = None

        self.boss_title = ""
        self.boss_subtitle = ""
        self.boss_title_alpha = 0
        self.boss_title_timer = 0
        self.boss_title_fade_out_time = 1.0  # duration of fade out
        self._boss_title_finished = False
        self.boss_font = pygame.font.SysFont("serif", 48)
        self.boss_subfont = pygame.font.SysFont("serif", 28)

    def apply(self, target):
        if isinstance(target, pygame.Rect):
            return target.move(self.offset)
        elif isinstance(target, (pygame.Vector2, tuple)):
            return pygame.Vector2(target) + self.offset
        return target

    def reverse(self, pos):
        return (pos[0] + self.offset.x, pos[1] + self.offset.y)

    def is_following(self):
        return self.mode == CameraMode.FOLLOW

    def show_boss_title(self, name, subtitle=""):
        self.boss_title = name
        self.boss_subtitle = subtitle
        self.boss_title_alpha = 0
        self._boss_title_finished = False

    def shake(self, magnitude=8, duration=0.25):
        self.shake_magnitude = magnitude
        self.shake_timer = duration
        self.shake_duration = duration

    def center_on(self, rect):
        self._base_offset.x = -rect.centerx + self.viewport_width // 2
        self._base_offset.y = -rect.centery + self.viewport_height // 2

    def _hold_on(self, target_rect, duration=1.0):
        self.mode = CameraMode.HOLD
        self.hold_target_rect = target_rect
        self.hold_timer = duration

    def begin_pan_to(self, target_rect, duration=2.5, return_to_rect=None, hold_duration=1.0):
        self.mode = CameraMode.PAN
        self.pan_target_rect = target_rect
        self.pan_timer = duration
        self.pan_duration = duration
        self._pan_start_offset = self._base_offset.copy()
        
        self._return_target = return_to_rect
        self._hold_duration = hold_duration

    def _clear_boss_title(self):
        self._boss_title_finished = True
        self.boss_title_alpha = 0

    def _update_boss_title(self, dt):
        if self._boss_title_finished:
            return

        # Fading in during initial pan
        if self.mode == CameraMode.PAN and self.boss_title_alpha < 255:
            progress = 1.0 - (self.pan_timer / self.pan_duration)
            self.boss_title_alpha = min(255, int(255 * progress))

        # Holding full or fading out during hold
        elif self.mode == CameraMode.HOLD:
            if self.hold_timer <= self.boss_title_fade_out_time:
                fade_out_progress = max(0, self.hold_timer / self.boss_title_fade_out_time)
                self.boss_title_alpha = int(255 * fade_out_progress)

        # Any other mode = clear title
        elif self.mode not in (CameraMode.PAN, CameraMode.HOLD):
            self._clear_boss_title()

    def _reset_pan_state(self):
        self.pan_target_rect = None
        self.hold_target_rect = None
        self._return_target = None
        self._hold_duration = 0

    def _end_pan(self):
        self.mode = CameraMode.FOLLOW
        self._reset_pan_state()

    def _update_follow(self, player_rect):
        if player_rect:
            self.center_on(player_rect)

    def _update_pan_to_target(self, dt):
        if not self.pan_target_rect:
            self._end_pan()
            return

        progress = 1.0 - (self.pan_timer / self.pan_duration)
        progress = max(0.0, min(progress, 1.0))

        desired_offset = pygame.Vector2(
            -self.pan_target_rect.centerx + self.viewport_width // 2,
            -self.pan_target_rect.centery + self.viewport_height // 2
        )

        self._base_offset = self._pan_start_offset.lerp(desired_offset, progress)

        self.pan_timer -= dt

        if self.pan_timer <= 0:
            if self._return_target:
                self._hold_on(self.pan_target_rect, duration=self._hold_duration)
            else:
                self._end_pan()

    def _update_hold_on_target(self, dt):
        if not self.hold_target_rect:
            self._end_pan()
            return

        self.center_on(self.hold_target_rect)
        self.hold_timer -= dt

        if self.hold_timer <= 0:
            self._clear_boss_title()

            if self._return_target:
                self.begin_pan_to(self._return_target, self.pan_duration)
                self._return_target = None
            else:
                self._end_pan()

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
        if self.mode == CameraMode.PAN:
            self._update_pan_to_target(dt)
        elif self.mode == CameraMode.FOLLOW:
            self._update_follow(player_rect)
        elif self.mode == CameraMode.HOLD:
            self._update_hold_on_target(dt)

        self._update_boss_title(dt)

        self._apply_shake(dt)