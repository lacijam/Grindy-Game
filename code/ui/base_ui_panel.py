import pygame
from ui.scrollable_panel import ScrollablePanel

class BaseUIPanel:
    def __init__(self, title, font, x, y, width, height):
        self.title = title
        self.font = font
        self.panel_x = x
        self.panel_y = y
        self.panel_width = width
        self.panel_height = height
        self.padding = 12
        self.content_x = self.padding
        self.content_width = self.panel_width - self.padding * 2
        self.panel = ScrollablePanel(x, y + 80, width, height - 120)
        self.close_rect = None

    def handle_scroll(self, event):
        self.panel.handle_scroll(event)

    def handle_mouse_click(self, pos):
        if self.close_rect and self.close_rect.collidepoint(pos):
            return "close"
    
    def handle_keydown(self, event):
        raise NotImplementedError("handle_keydown must be implemented in subclasses")

    def set_scrollable_panel_start_y(self, y):
        self.panel.rect.y = y

    def get_panel_scroll_context(self, screen):
        content_area = self.panel.rect
        content_surface = self.panel.apply_clip(screen)
        scroll_y = -self.panel.scroll_offset
        return content_area, content_surface, scroll_y
    
    def get_item_rect(self, y, height=36, margin=0):
        rect = pygame.Rect(self.content_x, y, self.content_width, height)
        return rect, height + margin
    
    def get_section_rect(self, y, height=36, margin=0):
        rect = pygame.Rect(self.padding, y, self.panel_width - self.padding * 2, height)
        return rect, height + margin

    def update(self):
        pass

    def draw_frame(self, screen):
        pygame.draw.rect(screen, (30, 30, 30), (self.panel_x, self.panel_y, self.panel_width, self.panel_height))
        pygame.draw.rect(screen, (200, 200, 200), (self.panel_x, self.panel_y, self.panel_width, self.panel_height), 2)

        title_surf = self.font.render(self.title, True, (255, 255, 255))
        screen.blit(title_surf, (self.panel_x + 16, self.panel_y + 12))

        self.close_rect = pygame.Rect(self.panel_x + self.panel_width - 32, self.panel_y + 12, 20, 20)
        mouse_pos = pygame.mouse.get_pos()
        hover = self.close_rect.collidepoint(mouse_pos)

        pygame.draw.rect(screen, (150, 50, 50) if hover else (100, 30, 30), self.close_rect)
        x_surf = self.font.render("X", True, (255, 255, 255))
        screen.blit(x_surf, (
            self.close_rect.centerx - x_surf.get_width() // 2,
            self.close_rect.centery - x_surf.get_height() // 2
        ))