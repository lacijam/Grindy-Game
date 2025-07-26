import pygame

from base_ui_panel import BaseUIPanel
from draw_helpers import draw_collapsible_section, draw_button, toggle_category_state
from tooltip_builder import queue_tooltip
from gamestate import GameState
from constants import *
from utils import to_panel_space
from format import get_colour_for_type, get_difficulty_colour

class TaskUI(BaseUIPanel):
    def __init__(self, task_manager, font, message_log):
        super().__init__("Tasks", font, 20, 40, 550, SCREEN_HEIGHT - 80)
        self.task_manager = task_manager
        self.message_log = message_log
        self.category_states = {
            "available": True,
            "unavailable": False,
            "completed": False
        }
        self.item_rects = []

        self.selected_difficulty_filter = "all"
        self.selected_task_type_filter = "all"

        self.difficulty_filter_buttons = [
            ("All", "all"),
            ("Easy", "easy"),
            ("Medium", "medium"),
            ("Hard", "hard"),
            ("Expert", "expert"),
            ("Master", "master"),
        ]

        self.task_type_filter_buttons = [
            ("All", "all"),
            ("Kill", "kill"),
            ("Gather", "gather"),
            ("Craft", "craft"),
            ("Level", "reach_level"),
        ]

        self.selected_sort_mode = "name"

        self.sort_mode_buttons = [
            ("Name", "name"),
            ("%", "progress"),
        ]

    def handle_keydown(self, event):
        pass

    def handle_mouse_click(self, mouse_pos):
        result = super().handle_mouse_click(mouse_pos)
        local_mouse = to_panel_space(mouse_pos, self.panel.rect)

        for rect, item_id, category in self.item_rects:
            if rect.collidepoint(local_mouse):
                if item_id is None:
                    toggle_category_state(self.category_states, category)
                else:
                    for task in self.task_manager.tasks:
                        if task.id == item_id and task.ready_to_claim:
                            self.task_manager.claim_task(task.id)
                return result

    def draw(self, screen):
        self.draw_frame(screen)

        self.item_rects.clear()

        content_area, content_surface, scroll_y = self.get_panel_scroll_context(screen)
        mouse_pos = pygame.mouse.get_pos()
        local_mouse = to_panel_space(mouse_pos, self.panel.rect)

        x = self.panel_x + self.padding
        y = self.panel_y + 40

        self.selected_difficulty_filter = self._draw_filter_button_row(
            screen, x, y, self.difficulty_filter_buttons, self.selected_difficulty_filter, get_difficulty_colour
        )

        y += 30
        self.selected_task_type_filter = self._draw_filter_button_row(
            screen, x, y, self.task_type_filter_buttons, self.selected_task_type_filter, get_colour_for_type
        )

        y += 30
        self.selected_sort_mode = self._draw_filter_button_row(
            screen, x, y, self.sort_mode_buttons, self.selected_sort_mode, lambda v: (150, 150, 150)
        )

        y += 30
        self.set_scrollable_panel_start_y(y)
        y = scroll_y

        categories = self.task_manager.get_tasks_by_category()

        for category in ["available", "unavailable", "completed"]:
            section_rect, dy = self.get_section_rect(y, height=36)
            draw_collapsible_section(content_surface, self.font, local_mouse, section_rect, category.title(), self.category_states.get(category, True))
            self.item_rects.append((section_rect, None, category))

            y += dy + 10

            sorted_tasks = sorted(categories[category], key=lambda t: self.get_task_sort_key(t))
            filtered_tasks = self._filter_tasks(sorted_tasks)

            if self.category_states.get(category, True):
                for task in filtered_tasks:
                    task_rect, dy = self.get_item_rect(y)

                    difficulty_col = get_difficulty_colour(task.difficulty)

                    if task.type in {"kill", "gather", "craft"}:
                        count = task.count
                        display_progress = min(task.progress, count)
                        label = f"{task.name} ({display_progress}/{count})"
                    else:
                        label = task.name

                    border_col = (100, 100, 100)
                    border_thickness = 2

                    if task.ready_to_claim:
                        difficulty_col = (255, 255, 255)
                        border_col = (255, 200, 0)
                        border_thickness = 4

                    is_hovered = draw_button(content_surface, task_rect, label, self.font, local_mouse,
                                             base_col=difficulty_col,
                                             border_col=border_col,
                                             border_thickness=border_thickness)

                    if is_hovered:
                        queue_tooltip({
                            "type": "task",
                            "data": task,
                            "position": mouse_pos,
                            "required_states": {GameState.TASKS}
                        })

                    self.item_rects.append((task_rect, task.id, category))

                    y += dy + 4

        pygame.draw.rect(screen, (80, 80, 80), content_area, 2)
        screen.blit(content_surface, content_area.topleft)

    def _draw_filter_button_row(self, screen, x, y, button_list, selected_value, get_colour_fn):
        mouse_pos = pygame.mouse.get_pos()
        result = selected_value

        for label, value in button_list:
            base_col = get_colour_fn(value) if value != "all" else (100, 100, 100)
            is_selected = (selected_value == value)
            button_rect = pygame.Rect(x, y, 80, 24)
            is_hovered = draw_button(screen, button_rect, label, self.font, mouse_pos,
                                     base_col=base_col if not is_selected else (255, 255, 255))
            if is_hovered and pygame.mouse.get_pressed()[0]:
                result = value

            x += 85

        return result

    def get_task_sort_key(self, task):
        if self.selected_sort_mode == "progress":
            count = task.count
            progress = min(task.progress, count)
            return -(progress / count) if count else 0
        else:
            return task.name

    def _filter_tasks(self, tasks):
        filtered_tasks = []

        for task in tasks:
            if self.selected_difficulty_filter != "all" and task.difficulty != self.selected_difficulty_filter:
                continue

            if self.selected_task_type_filter != "all" and task.type != self.selected_task_type_filter:
                continue

            filtered_tasks.append(task)

        return filtered_tasks
