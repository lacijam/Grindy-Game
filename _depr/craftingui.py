import pygame

from collections import defaultdict
from recipe_data import CRAFTING_RECIPES
from gamestate import GameState
from utils import *
from draw_helpers import *
from item_data import *
from tooltip_builder import queue_tooltip
from base_ui_panel import BaseUIPanel

# Crafting UI Layout
CRAFTING_TOGGLE_X = 320
CRAFTING_TOGGLE_Y = 90
CRAFTING_TOGGLE_OFF_COLOUR = (100, 100, 100)
CRAFTING_TOGGLE_ON_COLOUR = (100, 180, 100)

CRAFTING_CONTENT_START_Y = 130

CRAFTING_UNLOCKED_COLOUR = (100, 255, 100)
CRAFTING_LOCKED_COLOUR = (60, 60, 60)
CRAFTING_INSUFFICIENT_COLOUR = (100, 100, 100)

CATEGORY_BUTTON_HEIGHT = 30
CATEGORY_BUTTON_Y_SPACING = 35

RECIPE_BUTTON_X = 190
RECIPE_BUTTON_WIDTH = 280
RECIPE_BUTTON_HEIGHT = 30
RECIPE_BUTTON_Y_SPACING = 35

class CraftingUI(BaseUIPanel):
    def __init__(self, player, font, sound_manager):
        super().__init__("Crafting", font, 100, 80, 480, 600)
        self.collapsed_categories = {}
        self.crafting_buttons = []
        self.collapse_buttons = []
        self.selected_item_id = None
        self.show_all_recipes = False
        self.player = player
        self.sound_manager = sound_manager

    def handle_mouse_click(self, mouse_pos):
        result = super().handle_mouse_click(mouse_pos)

        if self.show_all_button_rect and self.show_all_button_rect.collidepoint(mouse_pos):
            self.show_all_recipes = not self.show_all_recipes
            self.sound_manager.queue("button_click")
            return result

        local_mouse = to_panel_space(mouse_pos, self.panel.rect)

        for rect, category in self.collapse_buttons:
            if rect.collidepoint(local_mouse):
                toggle_category_state(self.collapsed_categories, category)
                return result

        for rect, recipe in self.crafting_buttons:
            if rect.collidepoint(local_mouse):
                if not recipe_is_unlocked(recipe, self.player):
                    return result
                if all(self.player.inventory.items.get(item, 0) >= count for item, count in recipe["requires"].items()):
                    for item, count in recipe["requires"].items():
                        self.player.inventory.remove_item(item, count)
                    for item, count in recipe["produces"].items():
                        self.player.inventory.add_item(item, count)

                return result
        
        return result

    def handle_keydown(self, event):
        pass

    def draw(self, screen):
        self.draw_frame(screen)

        mouse_pos = pygame.mouse.get_pos()
        local_mouse = to_panel_space(mouse_pos, self.panel.rect)

        # Show All toggle
        self.show_all_button_rect = pygame.Rect(CRAFTING_TOGGLE_X, CRAFTING_TOGGLE_Y, 220, 30)
        toggle_text = "Show All Recipes" if not self.show_all_recipes else "Show Available Only"
        toggle_colour = CRAFTING_TOGGLE_OFF_COLOUR if not self.show_all_recipes else CRAFTING_TOGGLE_ON_COLOUR
        draw_button(screen, self.show_all_button_rect, toggle_text, self.font, mouse_pos, toggle_colour)

        # Group and draw recipes by category
        self.crafting_buttons.clear()
        self.collapse_buttons.clear()

        by_category = defaultdict(list)
        for recipe in CRAFTING_RECIPES:
            if self.show_all_recipes or recipe_is_unlocked(recipe, self.player):
                by_category[recipe["category"]].append(recipe)

        content_area, content_surface, scroll_y = self.get_panel_scroll_context(screen)
        y = scroll_y

        self.set_scrollable_panel_start_y(self.panel_y + 50)

        for category, recipes in by_category.items():
            collapsed = self.collapsed_categories.get(category, False)
            cat_rect, delta_y = self.get_section_rect(y, margin=6)
            draw_collapsible_section(
                content_surface,
                self.font,
                local_mouse,
                cat_rect,
                category,
                not self.collapsed_categories.get(category, False)
            )
            self.collapse_buttons.append((cat_rect, category))
            y += delta_y

            if collapsed:
                continue

            for recipe in recipes:
                rect = pygame.Rect(self.content_x, y, RECIPE_BUTTON_WIDTH, RECIPE_BUTTON_HEIGHT)
                has_materials = all(
                    self.player.inventory.items.get(item, 0) >= count
                    for item, count in recipe["requires"].items()
                )
                unlocked = recipe_is_unlocked(recipe, self.player)
                if not unlocked:
                    colour = CRAFTING_LOCKED_COLOUR
                elif has_materials:
                    colour = CRAFTING_UNLOCKED_COLOUR
                else:
                    colour = CRAFTING_INSUFFICIENT_COLOUR

                # send panel space coords again
                draw_button(content_surface, rect, recipe["name"], self.font, local_mouse, colour)
                self.crafting_buttons.append((rect, recipe))

                if rect.collidepoint(local_mouse):
                    queue_tooltip({
                        "type": "recipe",
                        "data": recipe,  # pass the raw recipe dict directly
                        "position": mouse_pos,
                        "required_states": {GameState.CRAFTING}
                    })

                    output_id = next(iter(recipe.get("produces", {})), None)

                    output_item_data = ItemFullData(
                        output_id,
                        ITEMS.get(output_id, {}),
                        {},
                        False
                    )

                    queue_tooltip({
                        "type": "item",
                        "data": output_item_data,
                        "position": (mouse_pos[0] + 280, mouse_pos[1]),
                        "required_states": {GameState.CRAFTING}
                    })

                y += RECIPE_BUTTON_Y_SPACING
        
        # Draw content to screen
        screen.blit(content_surface, content_area.topleft)