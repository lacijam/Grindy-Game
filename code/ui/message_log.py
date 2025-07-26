import time
import pygame

from format import get_colour_for_type
from ui.scrollable_panel import ScrollablePanel
from constants import SCREEN_HEIGHT
from draw_helpers import draw_typed_text

class MessageLog:
    def __init__(self, font, max_history=100, fade_delay=5):
        self.font = font
        self.panel = ScrollablePanel(
            x=20,
            y=SCREEN_HEIGHT - 200,
            width=520,
            height=170
        )
        self.max_history = max_history
        self.fade_delay = fade_delay

        self.messages = []
        self.last_message_time = 0
        self.entered_scroll_view = False

    def _resolve_colours(self, pairs):
        return [(text, get_colour_for_type(typ) if isinstance(typ, str) else typ) for text, typ in pairs]

    def _render_messages(self, messages, alpha, base_y, bottom_up=False):
        panel_rect = self.panel.rect
        panel_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        panel_surf.fill((100, 100, 100, alpha * 50 // 255))

        y = base_y
        messages_iter = reversed(messages) if bottom_up else messages

        for message in messages_iter:
            line_height = self.font.get_height()

            if bottom_up:
                y -= line_height + 4
            else:
                if y > panel_rect.height:
                    break

            draw_typed_text(panel_surf, self.font, message, x=10, y=y, alpha=alpha)

            if not bottom_up:
                y += line_height + 4

        return panel_surf

    def _calculate_fade_alpha(self):
        time_since = time.time() - self.last_message_time
        fade_duration = 1.0

        if time_since >= self.fade_delay:
            return 0
        if time_since >= self.fade_delay - fade_duration:
            t = (time_since - (self.fade_delay - fade_duration)) / fade_duration
            return int(255 * (1 - t))
        return 255

    def _calculate_total_content_height(self):
        line_heights = [
            max(self.font.size(text)[1] for text, _ in msg) + 4
            for msg in self.messages
        ]
        return sum(line_heights)

    def _update_scroll_offset(self, total_content_height):
        max_scroll = max(0, total_content_height - self.panel.rect.height)
        self.panel.scroll_offset = min(self.panel.scroll_offset, max_scroll)

    def queue(self, message):
        self.last_message_time = time.time()

        self.messages.append(self._resolve_colours(message))
        if len(self.messages) > self.max_history:
            self.messages.pop(0)

    def handle_scroll(self, event):
        self.panel.handle_scroll(event)

    def update(self):
        pass

    def draw_floating(self, surface):
        if self.panel.rect.collidepoint(pygame.mouse.get_pos()):
            self.last_message_time = time.time()

        alpha = self._calculate_fade_alpha()
        if alpha == 0:
            return

        y = self.panel.rect.height - 10
        surf = self._render_messages(self.messages[-6:], alpha, base_y=y, bottom_up=True)
        surface.blit(surf, self.panel.rect.topleft)
        pygame.draw.rect(surface, (80, 80, 80), self.panel.rect, width=2)

    def draw_scrollable(self, surface):
        total_content_height = self._calculate_total_content_height()

        if not self.entered_scroll_view:
            self.panel.scroll_offset = max(0, total_content_height - self.panel.rect.height)
            self.entered_scroll_view = True

        self._update_scroll_offset(total_content_height)

        base_y = -self.panel.scroll_offset
        surf = self._render_messages(self.messages, 255, base_y=base_y)

        surface.blit(surf, self.panel.rect.topleft)
        pygame.draw.rect(surface, (80, 80, 80), self.panel.rect, width=2)

    def clear(self):
        self.messages.clear()
