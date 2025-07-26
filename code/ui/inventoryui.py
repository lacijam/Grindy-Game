import pygame

from gamestate import GameState
from utils import *
from draw_helpers import *
from collections import defaultdict
from data.item_data import *
from ui.tooltip_builder import *
from ui.base_ui_panel import BaseUIPanel
from data.enchantment_data import ENCHANTMENT_DATA

INVENTORY_SORT_QTY_BTN_X = 340
INVENTORY_SORT_QTY_BTN_Y = 90
INVENTORY_SORT_QTY_BTN_WIDTH = 50
INVENTORY_SORT_QTY_BTN_HEIGHT = 30
INVENTORY_SORT_NAME_BTN_X = 400
INVENTORY_SORT_NAME_BTN_Y = 90
INVENTORY_SORT_NAME_BTN_WIDTH = 35
INVENTORY_SORT_NAME_BTN_HEIGHT = 30
INVENTORY_SORT_BTN_ACTIVE_COLOUR = (120, 200, 120)
INVENTORY_SORT_BTN_INACTIVE_COLOUR = (80, 80, 80)
SORT_ASCENDING_LABEL = "123"
SORT_DESCENDING_LABEL = "321"
INVENTORY_LIST_START_Y = 30
INVENTORY_CATEGORY_HEIGHT = 30
INVENTORY_CATEGORY_Y_SPACING = 35
INVENTORY_ITEM_WIDTH = 300
INVENTORY_ITEM_HEIGHT = 25
INVENTORY_HOTBAR_SELECTED_HIGHLIGHT = (255, 255, 100, 60) 
INVENTORY_ITEM_Y_SPACING = 28

class InventoryUI(BaseUIPanel):
    def __init__(self, player, font, sound_manager):
        super().__init__("Inventory", font, 100, 80, 480, 600)
        self.player = player
        self.equip_rects = []
        self.collapsed_categories = {}
        self.sort_mode = "name"
        self.sort_ascending = True
        self.sound_manager = sound_manager

    def handle_mouse_click(self, mouse_pos):
        result = super().handle_mouse_click(mouse_pos)

        if self.sort_name_button_rect and self.sort_name_button_rect.collidepoint(mouse_pos):
            self.sort_mode = 'name'
            self.sort_ascending = True
            self.sound_manager.queue("button_click")
            return result
        if self.sort_qty_button_rect and self.sort_qty_button_rect.collidepoint(mouse_pos):
            if self.sort_mode == 'quantity':
                self.sort_ascending = not self.sort_ascending
            else:
                self.sort_mode = 'quantity'
                self.sort_ascending = True

            self.sound_manager.queue("button_click")
            
            return result

        for slot, slot_rect in self.equip_rects:
            if slot_rect.collidepoint(mouse_pos):
                if self.player.equipment.slots.get(slot):
                    self.player.equipment.unequip(slot)
                    self.sound_manager.queue("item_equip")
                return result

        local_mouse = to_panel_space(mouse_pos, self.panel.rect)

        for rect, item_id, category in self.item_rects:
            if rect.collidepoint(local_mouse):
                if item_id is None:
                    toggle_category_state(self.collapsed_categories, category)
                else:
                    item_full_data = self.player.inventory.get_item_full_data(item_id)
                    base_data = item_full_data.base_data
                    metadata = item_full_data.metadata

                    if base_data.get("slot"):
                        self.player.equipment.equip(item_id, metadata)
                        self.sound_manager.queue("item_equip")

                return result
        
        return result

    def handle_keydown(self, key):
        if key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
            index = key - pygame.K_1
            item_id = self.hovered_item_id
            if not item_id:
                return

            base_id = self.player.inventory.get_base_id(item_id)
            item = ITEMS.get(base_id, {})
            if "skill" in item:
                self.player.inventory.assign_to_hotbar(item_id, index)

    def update(self):
        self.hovered_item_id = None
        self.hovered_category = None

    def draw(self, screen):
        self.hovered_item_id = None
        mouse_pos = pygame.mouse.get_pos()

        self.equip_rects.clear()

        panel_x = self.panel_x + self.panel_width + 16

        self.equip_rects = self._draw_equipment_panel(
            screen,
            self.font,
            self.player,
            panel_x,
            self.panel_y,
            VIEWPORT_WIDTH - panel_x - 16,
            self.panel_height,
            self.padding
        )

        self.draw_frame(screen)

        name_colour = INVENTORY_SORT_BTN_ACTIVE_COLOUR if self.sort_mode == 'name' else INVENTORY_SORT_BTN_INACTIVE_COLOUR
        qty_colour = INVENTORY_SORT_BTN_ACTIVE_COLOUR if self.sort_mode == 'quantity' else INVENTORY_SORT_BTN_INACTIVE_COLOUR

        self.sort_name_button_rect = pygame.Rect(INVENTORY_SORT_NAME_BTN_X, INVENTORY_SORT_NAME_BTN_Y, INVENTORY_SORT_NAME_BTN_WIDTH, INVENTORY_SORT_NAME_BTN_HEIGHT)
        draw_button(screen, self.sort_name_button_rect, "Aa", self.font, mouse_pos, name_colour)

        qty_text = SORT_ASCENDING_LABEL if self.sort_ascending else SORT_DESCENDING_LABEL
        self.sort_qty_button_rect = pygame.Rect(INVENTORY_SORT_QTY_BTN_X, INVENTORY_SORT_QTY_BTN_Y, INVENTORY_SORT_QTY_BTN_WIDTH, INVENTORY_SORT_QTY_BTN_HEIGHT)
        draw_button(screen, self.sort_qty_button_rect, qty_text, self.font, mouse_pos, qty_colour)

        by_category = defaultdict(list)
        for item_id, count in self.player.inventory.items.items():
            category = ITEMS.get(item_id, {}).get("category", "Misc")
            by_category[category].append((item_id, count))

        for instance_id, item_instance in self.player.inventory.item_instances.items():
            item_id = item_instance.item_id
            category = ITEMS.get(item_id, {}).get("category", "Misc")

            enchantments = item_instance.metadata.get("enchantments", [])

            ui_item_id = f"{item_id}__instance__{instance_id}"
            by_category[category].append((ui_item_id, 1))

        self.item_rects = []

        mouse_pos = pygame.mouse.get_pos()
        local_mouse = to_panel_space(mouse_pos, self.panel.rect)

        content_area, content_surface, scroll_y = self.get_panel_scroll_context(screen)
        y = scroll_y

        self.set_scrollable_panel_start_y(self.panel_y + 50)

        for category, items in by_category.items():
            collapsed = self.collapsed_categories.get(category, False)
            cat_rect, delta_y = self.get_section_rect(y, margin=10)
            draw_collapsible_section(
                content_surface,
                self.font,
                local_mouse,
                cat_rect,
                category,
                not self.collapsed_categories.get(category, False)
            )
            self.item_rects.append((cat_rect, None, category))
            y += delta_y

            if collapsed:
                continue

            if self.sort_mode == 'name':
                items.sort(key=lambda x: x[0].lower())
            elif self.sort_mode == 'quantity':
                items.sort(key=lambda x: x[1], reverse=not self.sort_ascending)

            for item_id, count in items:
                # Default values
                item_id_clean = item_id
                item_name = "UNKNOWN"
                enchantments = []

                if "__instance__" in item_id:
                    base_item_id, rest = item_id.split("__instance__", 1)
                    instance_id = int(rest)
                    item_id_clean = base_item_id
                    item_name = ITEMS.get(item_id_clean, {}).get("name", item_id_clean.title())

                    # Get instance metadata
                    instance = self.player.inventory.item_instances.get(instance_id)
                    enchantments = instance.metadata.get("enchantments", []) if instance else []
                else:
                    item_name = ITEMS.get(item_id_clean, {}).get("name", item_id_clean.title())

                # Add * if item has enchantments
                item_name += "*" if enchantments else ""

                # Draw item
                item_data = ITEMS.get(item_id_clean, NULL_ITEM)
                item_rarity = item_data["rarity"]
                item_colour = get_rarity_colour(item_rarity)

                item_rect, delta_y = self.get_item_rect(y)
                text = self.font.render(f"{item_name} x{count}", True, item_colour)
                text_rect = self._get_centered_rect_around_text(text, (item_rect.x, item_rect.y))

                if item_rect.collidepoint(local_mouse):
                    pygame.draw.rect(content_surface, (80, 80, 80), text_rect)

                content_surface.blit(text, (item_rect.x, item_rect.y))

                selected_index = self.player.inventory.selected_hotbar_index
                selected_item_id = self.player.inventory.hotbar[selected_index] if 0 <= selected_index < len(self.player.inventory.hotbar) else None

                if item_id == selected_item_id:
                    highlight = pygame.Surface((text_rect.width, text_rect.height), pygame.SRCALPHA)
                    highlight.fill(INVENTORY_HOTBAR_SELECTED_HIGHLIGHT)
                    content_surface.blit(highlight, (text_rect.x, text_rect.y))

                self.item_rects.append((text_rect, item_id, category)) # pass the text rect rather than full width

                for i, hotbar_item in enumerate(self.player.inventory.hotbar):
                    if hotbar_item == item_id:
                        number_surf = self.font.render(str(i + 1), True, (255, 255, 255))
                        content_surface.blit(number_surf, (item_rect.right - number_surf.get_width() - 4, item_rect.y + 2))
                        break

                if text_rect.collidepoint(local_mouse):
                    self.hovered_item_id = item_id
                    queue_tooltip({
                        "type": "item",
                        "data": self.player.inventory.get_item_full_data(item_id),
                        "position": (mouse_pos[0], mouse_pos[1]),
                        "required_states": {GameState.INVENTORY}
                    })

                y += delta_y

        screen.blit(content_surface, content_area.topleft)
    
    def _get_centered_rect_around_text(self, text_surf, anchor_pos, padding=4):
        """Returns a pygame.Rect centered around the rendered text with optional padding."""
        text_width = text_surf.get_width()
        text_height = text_surf.get_height()
        return pygame.Rect(
            anchor_pos[0] - padding,
            anchor_pos[1] - padding,
            text_width + padding * 2,
            text_height + padding * 2
        )
    
    def _draw_equipment_panel(self, surface, font, player, x, y, width, height, padding = 10):
        pygame.draw.rect(surface, (20, 20, 20), (x, y, width, height))
        pygame.draw.rect(surface, (100, 100, 100), (x, y, width, height), 2)

        label_surf = font.render("Equipped Items", True, (255, 255, 255))
        surface.blit(label_surf, (x + 10, y + 10))

        rects = []
        slot_width = width - 20
        slot_height = 36
        slot_y = y + 40

        mouse_pos = pygame.mouse.get_pos()

        for slot in player.equipment.SLOTS:
            label = f"{slot.title()}:"
            item_colour = (255, 255, 255)

            slot_rect = pygame.Rect(x + padding, slot_y, slot_width, slot_height)  # ← define FIRST!

            slot_entry = player.equipment.slots[slot]
            if slot_entry:
                item_id = slot_entry.item_id
                metadata = slot_entry.metadata

                base_id = player.inventory.get_base_id(item_id)
                item_base_data = ITEMS.get(base_id, {})
                item_name = item_base_data.get("name", "Unnamed Item")
                item_rarity = item_base_data.get("rarity", "common")

                enchantments = metadata.get("enchantments", [])
                item_name += "*" if enchantments else ""

                label = f"{slot.title()}: {item_name}"
                item_colour = get_rarity_colour(item_rarity)

                item_full_data = ItemFullData(
                    item_id=item_id,
                    base_data=ITEMS.get(player.inventory.get_base_id(item_id), {}),
                    metadata=metadata,
                    is_instance=player.inventory.is_item_instance(item_id)
                )

                if item_id and slot_rect.collidepoint(mouse_pos):
                    queue_tooltip({
                        "type": "item",
                        "data": item_full_data,
                        "position": mouse_pos,
                        "required_states": {GameState.INVENTORY}
                    })

            text_surf = font.render(label, True, item_colour)

            is_hovered = slot_rect.collidepoint(mouse_pos)
            if is_hovered:
                pygame.draw.rect(surface, (40, 40, 40), slot_rect)

            surface.blit(text_surf, (slot_rect.x, slot_rect.y))

            rects.append((slot, slot_rect))
            slot_y += slot_height + 6

        y = self._draw_player_stats(surface, font, player, x, slot_y)

        # Draw Active Effects below player stats
        y += 20  # spacing
        active_effects_label = f"Active Effects ({len(player.stats.active_effects)})"
        active_effects_surf = font.render(active_effects_label, True, (255, 255, 255))
        surface.blit(active_effects_surf, (x + 10, y))

        # Add hover detection
        active_effects_rect = pygame.Rect(x + 10, y, active_effects_surf.get_width(), active_effects_surf.get_height())
        mouse_pos = pygame.mouse.get_pos()
        if active_effects_rect.collidepoint(mouse_pos):
            # Build alphabetically sorted list of effect names
            effect_names = []
            for effect in player.stats.active_effects:
                effect_data = ABILITY_DATA.get(effect["id"])
                if not effect_data:
                    effect_data = ENCHANTMENT_DATA.get(effect["id"], {})
                name = effect_data.get("name", effect["id"].title())
                effect_names.append(name)

            effect_names.sort()

            # Build tooltip lines
            tooltip_lines = []
            for name in effect_names:
                tooltip_lines.append([(name, (180, 180, 255))])

            # Queue tooltip
            queue_tooltip({
                "type": "custom",
                "data": tooltip_lines,
                "position": (mouse_pos[0], mouse_pos[1]),
                "required_states": {GameState.INVENTORY},
            })

        return rects  # For hover detection

    def _draw_player_stats(self, surface, font, player, x, y, padding=10):
        mouse_pos = pygame.mouse.get_pos()
        
        stat_margin = 8

        for stat, value in player.stats.total_stats.items():
            label = get_stat_display_name(stat)
            fmt = get_stat_format(stat)
            value_str = fmt(value)
            colour = get_stat_colour(stat)

            text = f"{label}: {value_str}"
            surf = font.render(text, True, colour)

            # draw
            surface.blit(surf, (x + padding, y))

            # detect hover and queue tooltip
            stat_rect = pygame.Rect(x, y, surf.get_width(), surf.get_height())
            if stat_rect.collidepoint(mouse_pos):
                queue_tooltip({
                    "type": "stat",
                    "data": {
                        "label": label,
                        "base": player.stats.base_stats[stat],
                        "sources": player.stats.stat_sources.get(stat, []),
                    },
                    "position": (mouse_pos[0], mouse_pos[1]),
                    "required_states": {GameState.PLAYING, GameState.INVENTORY},
                    "stat": stat
                })
            
            y += surf.get_height() + stat_margin

        return y
