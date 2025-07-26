import pygame
from constants import *
from data.enemy_data import ENEMY_DATA
from utils import *
from ui.tooltip_builder import queue_tooltip
from format import format_drop_table_lines
from gamestate import GameState
from draw_helpers import *
from ui.base_ui_panel import BaseUIPanel

class BeastiaryUI(BaseUIPanel):
    def __init__(self, player, font):
        super().__init__("Beastiary", font, 20, 40, 400, SCREEN_HEIGHT - 80)
        self.player = player
        self.progress_bar_tooltips = []

    def update(self):
        self.progress_bar_tooltips.clear()

    def handle_keydown(self, event):
        pass

    def draw(self, screen):
        self.draw_frame(screen)

        padding = 12

        enemy_ids = list(ENEMY_DATA.keys())
        enemy_ids.sort(key=lambda eid: (eid not in self.player.discovered_enemies, eid))

        mouse_pos = pygame.mouse.get_pos()

        content_area, content_surface, scroll_y = self.get_panel_scroll_context(screen)
        y = scroll_y

        self.set_scrollable_panel_start_y(self.panel_y + 80)

        for enemy_id in enemy_ids:
            discovered = enemy_id in self.player.discovered_enemies
            data = ENEMY_DATA.get(enemy_id, {})

            name = data.get("name", enemy_id).title() if discovered else "??????"

            header_text = f"{name}"
            header = self.font.render(header_text, True, (255, 255, 255))
            content_surface.blit(header, (padding, y))
            y += header.get_height() + 4

            if discovered:
                drop_lines = format_drop_table_lines(data.get("drop_table", []))
                for line, colour in drop_lines:
                    surf = self.font.render(line, True, colour)
                    content_surface.blit(surf, (padding, y))
                    y += surf.get_height() + 2

                # Draw beastiary level progress bar
                kill_count = self.player.beastiary.get_enemy_kill_count(enemy_id)
                level, progress = get_beastiary_progress(enemy_id, kill_count)

                thresholds = ENEMY_DATA[enemy_id].get("beastiary", {}).get("thresholds", [])
                next_threshold = thresholds[level] if level < len(thresholds) else thresholds[-1]
                label = f"Kills: {kill_count}/{next_threshold}"
                bar_rect = pygame.Rect(padding, y, self.panel_width - 2 * padding, 24)

                draw_progress_bar(content_surface, bar_rect, progress,
                                colour=(120, 180, 255), text=label, font=self.font)
                
                y += bar_rect.height + 6

                global_rect = bar_rect.move(content_area.left, content_area.top)

                if global_rect.collidepoint(mouse_pos):
                    queue_tooltip({
                        "type": "beastiary_level",
                        "data": {
                            "enemy_id": enemy_id,
                            "progress": {
                                "level": level,
                                "kills": kill_count,
                                "thresholds": thresholds
                            }
                        },
                        "position": mouse_pos,
                        "required_states": {GameState.BEASTIARY}
                    })
            else:
                hint = self.font.render("Find and defeat this enemy to log it.", True, (160, 160, 160))
                content_surface.blit(hint, (padding * 2, y))
                y += hint.get_height() + 2

            y += padding

        screen.blit(content_surface, content_area.topleft)

        total = len(ENEMY_DATA)
        found = len(self.player.discovered_enemies)
        draw_completion_tracker(screen, self.panel_x, self.panel_y, self.panel_width, self.panel_height, found, total, self.font)

        # Total Beastiary Progress (below enemies list)
        total_level = self.player.beastiary.get_total_beastiary_level()
        max_total = self.player.beastiary.get_max_total_beastiary_level()  
        bar_width = self.panel_width - 24
        bar_rect = pygame.Rect(self.panel_x + 12, self.panel_y + 40, bar_width, 20)
        progress = min(total_level / max_total, 1.0)
        label = f"Total Beastiary Level: {total_level}"

        draw_progress_bar(screen, bar_rect, progress, colour=(200, 160, 255), text=label, font=self.font)

        if bar_rect.collidepoint(pygame.mouse.get_pos()):
            queue_tooltip({
                "type": "total_beastiary",
                "data": {
                    "label": "Beastiary Progress",
                    "level": total_level
                },
                "position": pygame.mouse.get_pos(),
                "required_states": {GameState.BEASTIARY}
            })