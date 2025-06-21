import pygame

from constants import *
from item_data import ITEMS
from format import *
from tooltip_builder import queue_tooltip
from gamestate import GameState
from player_inventory import ItemFullData

def draw_typed_text(surface, font, segments, x, y, alpha=255):
    current_x = x
    for text, colour in segments:
        surf = font.render(text, True, colour[:3]).convert_alpha()
        surf.set_alpha(alpha)
        surface.blit(surf, (current_x, y))
        current_x += surf.get_width()

def get_completion_bar_rect(panel_x, panel_y, panel_width, panel_height, padding=12, width=200, height=30):
    bar_x = panel_x + (panel_width - width) // 2
    bar_y = panel_y + panel_height - height - padding
    return pygame.Rect(bar_x, bar_y, width, height)

def draw_collapsible_section(surface, font, mouse_pos, rect, label, is_open):
    icon = "-" if is_open else "+"
    label_text = f"{icon} {label}"
    return draw_button(surface, rect, label_text, font, mouse_pos)

def toggle_category_state(category_dict, cat):
    category_dict[cat] = not category_dict.get(cat, False)

def draw_button(surface, rect, text, font, mouse_pos, base_col=(50, 50, 50), text_col=None, border_col=(100, 100, 100), border_thickness=2):
    is_hovered = rect.collidepoint(mouse_pos)

    hover_col = tuple(max(0, int(c * 0.5)) for c in base_col)

    bg_colour = hover_col if is_hovered else base_col

    pygame.draw.rect(surface, bg_colour, rect)
    pygame.draw.rect(surface, border_col, rect, border_thickness)

    if text_col is None:
        text_col = get_contrasting_text_colour(bg_colour)

    text_surf = font.render(text, True, text_col)
    text_x = rect.x + (rect.width - text_surf.get_width()) // 2
    text_y = rect.y + (rect.height - text_surf.get_height()) // 2
    surface.blit(text_surf, (text_x, text_y))

    return is_hovered

def draw_progress_bar(surface, rect, progress, colour, border_colour=(255,255,255), bg_colour=(40,40,40), text=None, font=None):
    pygame.draw.rect(surface, bg_colour, rect)  # full bar background
    pygame.draw.rect(surface, border_colour, rect, 1)  # border

    # Fill area: don't shrink height — just shrink width slightly to stay inside border
    fill_width = max(0, int(rect.width * progress))
    fill_rect = pygame.Rect(rect.left + 1, rect.top + 1, fill_width - 2, rect.height - 2)
    pygame.draw.rect(surface, colour, fill_rect)

    if text and font:
        label = font.render(text, True, (255, 255, 255))
        surface.blit(label, (
            rect.centerx - label.get_width() // 2,
            rect.centery - label.get_height() // 2
        ))

def draw_completion_tracker(screen, x, y, w, h, found, total, font):
    progress = found / total if total else 0
    label = f"{found}/{total} Discovered"
    bar_rect = get_completion_bar_rect(x, y, w, h)
    draw_progress_bar(screen, bar_rect, progress, (100, 200, 100), text=label, font=font)