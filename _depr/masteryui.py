import pygame
from item_data import ITEMS
from utils import *
from draw_helpers import *
from constants import SCREEN_HEIGHT
from tooltip_builder import *
from gamestate import GameState
from base_ui_panel import BaseUIPanel

class MasteryUI(BaseUIPanel):
    def __init__(self, player, font):
        super().__init__("Resource Mastery", font, 40, 40, 400, SCREEN_HEIGHT - 80)
        self.player = player
        self.progress_bar_tooltips = []
        self.total_masteries = sum(1 for item in ITEMS.values() if "max_mastery_level" in item)
        self.mastery_item_ids = [item_id for item_id, item in ITEMS.items() if "max_mastery_level" in item]

    def handle_keydown(self, event):
        pass

    def update(self):
        self.progress_bar_tooltips.clear()

    def draw(self, screen):
        self.draw_frame(screen)

        item_ids = [item_id for item_id, item in ITEMS.items() if "max_mastery_level" in item]
        item_ids.sort(key=lambda item_id: (item_id not in self.player.discovered_resources, item_id))

        entry_height = 50

        # Clipping area for scrollable entries
        content_area, content_surface, scroll_y = self.get_panel_scroll_context(screen)

        mouse_pos = pygame.mouse.get_pos()

        y = scroll_y

        self.set_scrollable_panel_start_y(self.panel_y + 80)

        for item_id in item_ids:
            discovered = item_id in self.player.discovered_resources
            count = self.player.mastery.get_resource_mastery_count(item_id)

            item = ITEMS.get(item_id, {})
            name = item.get("name", item_id).title() if discovered else "??????"

            label_surf = self.font.render(name, True, (255, 255, 255))
            content_surface.blit(label_surf, (self.padding, y))

            if discovered:
                level, progress, thresholds = get_resource_mastery_progress(item_id, count, self.player)
                next_threshold = thresholds[level] if level < len(thresholds) else thresholds[-1]
                text = f"Lv {level}   Collected: {count}/{next_threshold}"

                bar_rect = pygame.Rect(self.padding, y + label_surf.get_height() + 4, self.panel_width - 2 * self.padding, 24)
                draw_progress_bar(content_surface, bar_rect, progress, (100, 200, 100), text=text, font=self.font)

                y += bar_rect.height + 6

                global_rect = bar_rect.move(content_area.left, content_area.top)

                if global_rect.collidepoint(mouse_pos):
                    queue_tooltip({
                        "type": "mastery_level",
                        "data": {
                            "progress": {
                                "level": level,
                                "count": count,
                                "thresholds": thresholds
                            }
                        },
                        "position": mouse_pos,
                        "required_states": {GameState.MASTERY}
                    })

            y += entry_height

        # Draw content to screen
        screen.blit(content_surface, content_area.topleft)

        # Completion bar
        bar_rect = get_completion_bar_rect(
            self.panel_x, self.panel_y, self.panel_width, self.panel_height
        )

        found = self.player.mastery.get_resource_mastery_total_entries()
        draw_completion_tracker(screen, self.panel_x, self.panel_y, self.panel_width, self.panel_height, found, self.total_masteries, self.font)

        mouse_pos = pygame.mouse.get_pos()
        for tooltip in self.progress_bar_tooltips:
            if tooltip["rect"].collidepoint(mouse_pos):
                queue_tooltip({
                    "type": "mastery_level",
                    "data": {
                        "level": tooltip["level"],
                        "thresholds": tooltip["thresholds"],
                        "count": tooltip["count"],
                        "player": self.player
                    },
                    "position": (mouse_pos[0] + 16, mouse_pos[1] + 16),
                    "required_states": {GameState.MASTERY}
                })
                break

        # Resource Mastery Progress Bar
        total_level = self.player.mastery.get_total_resource_mastery_level()
        max_total = self.player.mastery.get_max_total_resource_mastery_level()  # You can change this if you want a cap or fixed scale
        bar_width = self.panel_width - 24
        bar_rect = pygame.Rect(self.panel_x + 12, self.panel_y + 40, bar_width, 20)
        progress = min((total_level / max_total), 1.0)
        draw_progress_bar(screen, bar_rect, progress, colour=(200, 160, 255), text=f"Total Resource Mastery Lv {total_level}", font=self.font)

        # Tooltip
        mouse = pygame.mouse.get_pos()
        if bar_rect.collidepoint(mouse):
            queue_tooltip({
                "type": "total_mastery",
                "data": {
                    "label": "Resource Mastery",
                    "level": total_level
                },
                "position": mouse,
                "required_states": {GameState.MASTERY}
            })