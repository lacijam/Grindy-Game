import pygame

class ScrollablePanel:
    def __init__(self, x, y, width, height, scroll_speed=24):
        self.rect = pygame.Rect(x, y, width, height)
        self.scroll_offset = 0
        self.scroll_speed = scroll_speed

    def handle_scroll(self, event):
        self.scroll_offset = max(0, self.scroll_offset - event.y * self.scroll_speed)

    def apply_clip(self, surface):
        return surface.subsurface(self.rect).copy()

    def reset_offset(self):
        self.scroll_offset = 0
