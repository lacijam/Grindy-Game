import pygame

from constants import *
from gamestate import GameState
from camera import Camera
from player import Player
from craftingui import CraftingUI
from inventoryui import InventoryUI
from beastiaryui import BeastiaryUI
from masteryui import MasteryUI
from task_ui import TaskUI
from task_manager import TaskManager
from item_data import *
from zone import Zone
from zone_data import ZONE_DATA
from zone_transition import ZoneTransition
from utils import *
from draw_helpers import *
from tooltip_context import TooltipContext
from tooltip_builder import *
from popup import Popup
from format import format_number_short, describe_stat_bonus, get_skill_colour
from sound_manager import SoundManager
from message_log import MessageLog
from pickup_log import PickupLog
from experience import *
from mastery_data import get_mastery_contribution_for_item

class Game:
    def __init__(self):
        self.font = pygame.font.SysFont(None, FONT_SIZE)

        self.state = GameState.PLAYING

        self.surface = pygame.Surface((VIEWPORT_WIDTH, VIEWPORT_HEIGHT))

        self.zones = {}
        self.current_zone = None
        self.zone_font = pygame.font.SysFont("serif", 48)
        self.zone_subtitle_font = pygame.font.SysFont("serif", 24)
        self.transition = ZoneTransition(VIEWPORT_WIDTH, VIEWPORT_HEIGHT, self.zone_font, self.zone_subtitle_font)
        self.load_zones()

        self.player = Player(0, 0, 30, self.current_zone)
        self.camera = Camera((-self.player.rect.x + VIEWPORT_WIDTH//2, -self.player.rect.y + VIEWPORT_HEIGHT//2), VIEWPORT_WIDTH, VIEWPORT_HEIGHT)
        
        self.pickup_log = PickupLog(self.font)
        self.message_log = MessageLog(font=self.font)

        self.damage_popups = []
        self.xp_popups = []

        self.sound_manager = SoundManager()

        self.tasks = TaskManager(self.player, self.message_log, self.sound_manager)
        self.task_ui = TaskUI(self.tasks, self.font, self.message_log)
        self._notified_unclaimed = False
        self._unclaimed_reminder_timer = 0
        
        self.craftingui = CraftingUI(self.player, self.font, self.tasks, self.sound_manager)
        self.inventoryui = InventoryUI(self.player, self.font, self.sound_manager)
        self.beastiary_ui = BeastiaryUI(self.player, self.font)
        self.mastery_ui = MasteryUI(self.player, self.font)

        self.damage_overlay_alpha = 0
        self.damage_overlay_decay_rate = 300

        self.mouse_held = False

        self._change_zone("starter_zone")

    def load_zones(self):
        for z in ZONE_DATA:
            self.zones[z["id"]] = Zone(
                id=z.get("id", "unknown"),
                size=z.get("size", 0),
                safe=z.get("safe", False),
                num_enemies=z.get("num_enemies"),
                enemy_spawn_table=z.get("enemy_spawn_table", None),
                num_resources=z.get("num_resources", 0),
                resource_node_spawn_table=z.get("resource_node_spawn_table", None),
                connections=z.get("connections", {}),
                name=z.get("name", "NONAME"),
                type=z.get("type", "combat"),
                requirements=z.get("requirements", {}),
            )
        
    def _change_zone(self, next_zone_id, exit_direction=None):
        if next_zone_id not in self.zones:
            print(f"Zone {next_zone_id} not loaded!")
            return

        # Set the current zone
        self.current_zone = self.zones[next_zone_id]
        self.player.zone = self.current_zone

        # Move player to entry point
        x, y = self.current_zone.get_entry_point(exit_direction)
        self.player.pos.x = x - self.player.rect.width // 2
        self.player.pos.y = y - self.player.rect.height // 2
        self.player.rect.topleft = (int(self.player.pos.x), int(self.player.pos.y))

        # Center camera and prepare zone state
        self.camera.center_on(self.player.rect)
        self.current_zone.prepare(self.player)

        # Handle safe zone message
        if self.current_zone.safe:
            if self.player.last_safe_zone_id != self.current_zone.id:
                self.message_log.queue([("Safe zone updated", "white")])
            self.player.update_last_safe_zone(self.current_zone.id)

        # Handle discovery
        if self.current_zone.id not in self.player.discovered_zones:
            self.player.discovered_zones.add(self.current_zone.id)
            self.message_log.queue([
                ("Discovered Zone: ", "white"),
                (self.current_zone.name, self.current_zone.type)
            ])

        # Handle boss zone intro
        if self.current_zone.type == "boss" and not self.current_zone.has_intro_played:
            boss_rect, boss_name, boss_subtitle = self.current_zone.get_boss_metadata()
            if boss_rect:
                self.camera.begin_pan_to(boss_rect, 1.0, self.player.rect, 1.0)
                self.camera.show_boss_title(boss_name, boss_subtitle)
                self.current_zone.has_intro_played = True

    def handle_zone_transition(self, dt):
        if not self.transition.is_active():
            next_zone_id, direction = self.current_zone.check_portal_trigger(
                self.player, self.zones
            )

            if next_zone_id:
                next_zone = self.zones[next_zone_id]

                if next_zone.type == "boss":
                    self.transition.begin(next_zone_id, direction, "")
                else:
                    self.transition.begin(next_zone_id, direction, next_zone.name)

        result = self.transition.update(dt)
        if result:
            zone_id, direction = result
            self._change_zone(zone_id, direction)

    def handle_player_death(self):
        self.player.hp = self.player.stats.total_stats["max_hp"]
        self._change_zone(self.player.last_safe_zone_id)
        self.message_log.queue("You died and returned to a safe zone.")

    def get_active_ui(self):
        if self.state == GameState.INVENTORY:
            return self.inventoryui
        elif self.state == GameState.CRAFTING:
            return self.craftingui
        elif self.state == GameState.BEASTIARY:
            return self.beastiary_ui
        elif self.state == GameState.MASTERY:
            return self.mastery_ui
        elif self.state == GameState.TASKS:
            return self.task_ui
        return None

    def handle_mouse_event(self, event):
        active_ui = self.get_active_ui()

        if event.type == pygame.MOUSEWHEEL:
            if active_ui:
                active_ui.handle_scroll(event)
            return

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.mouse_held = True
                if active_ui:
                    result = active_ui.handle_mouse_click(self.mouse_pos)
                    if result == "close":
                        self.state = GameState.PLAYING
                        self.sound_manager.queue("button_back")

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.mouse_held = False

    def handle_keydown_event(self, key):
        active_ui = self.get_active_ui()

        key_to_state_toggle = {
            pygame.K_TAB: GameState.INVENTORY,
            pygame.K_c: GameState.CRAFTING,
            pygame.K_b: GameState.BEASTIARY,
            pygame.K_m: GameState.MASTERY,
            pygame.K_p: GameState.PAUSED,
            pygame.K_SLASH: GameState.MESSAGE_LOG,
            pygame.K_t: GameState.TASKS
        }

        if key in key_to_state_toggle:
            target = key_to_state_toggle[key]
            self.state = GameState.PLAYING if self.state == target else target

            if target == GameState.MESSAGE_LOG and self.state != GameState.MESSAGE_LOG:
                self.message_log.entered_scroll_view = False

            return

        if active_ui:
            active_ui.handle_keydown(key)
            return
        
        if key == pygame.K_TAB:
            self.state = GameState.INVENTORY if self.state == GameState.PLAYING else GameState.PLAYING
            return
        if key == pygame.K_b:
            self.state = GameState.PLAYING if self.state == GameState.BEASTIARY else GameState.BEASTIARY
            return
        if key == pygame.K_p:
            if self.state == GameState.PAUSED:
                self.state = GameState.PLAYING
            elif self.state == GameState.PLAYING:
                self.state = GameState.PAUSED 
            return

        if key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5):
            index = key - pygame.K_1
            if 0 <= index < len(self.player.inventory.hotbar):
                self.player.change_active_item(index)
            return

    def _get_level_up_message(self, skill, new_level, desc):
        return [
            (f"{skill.capitalize()}", get_skill_colour(skill)),
            (" Level Up! Now Level ", "white"),
            (str(new_level), "number"),
            (" (", "white"),
            (f"+{desc['formatted']} ", get_colour_for_type("number")),
            (desc["label"], desc["colour"]),
            (")", "white"),
        ]

    def spawn_xp_popup(self, x, y, offset_y, label, colour):
        self.xp_popups.append(Popup(x, y + offset_y, label, colour=colour))
        return offset_y + 28

    def handle_gainxp(self, skill, amount, origin=None):
        if amount <= 0:
            return
        
        if origin is None:
            origin = self.player.rect.center

        x, y = origin
        key = (int(x), int(y))

        offset_y = self._popup_offsets.get(key, 0)

        old_level = self.player.skills.get_skill_level(skill)
        self.player.skills.gain_xp(skill, amount)
        new_level = self.player.skills.get_skill_level(skill)

        label = f"+{amount} XP"
        colour = SKILL_COLOURS.get(skill, (255, 255, 255))
        offset_y = self.spawn_xp_popup(x, y, offset_y, label, colour)

        if new_level > old_level:
            bonus_info = self.player.stats.level_up_bonuses.get(skill)
            if bonus_info:
                stat = bonus_info["stat"]
                per_level = bonus_info["per_level"]
                desc = describe_stat_bonus(stat, per_level)
            else:
                desc = {"label": "-", "colour": (255, 255, 255), "formatted": "-"}

                self.message_log.queue(self._get_level_up_message(skill, new_level, desc))

            self.tasks.handle_level_up(skill, new_level)

            self.message_log.queue([
                ("Skill", "white"),
                (" Level Up! ", "white"),
                (skill.title(), get_skill_colour(skill)),
                (" - Level ", "white"),
                (str(new_level), "number")
            ])

            self.sound_manager.queue("level_up_skill")

            offset_y = self.spawn_xp_popup(x, y, offset_y, "LEVEL UP!", colour)

        self._popup_offsets[key] = offset_y

    def _log_mastery_level_up(self, item_id, item, new_level, prev_level=0):
        name = item.get("name", item_id).title()
        for level in range(prev_level + 1, new_level + 1):
            self.message_log.queue([
                ("Mastery", get_colour_for_type("mastery")),
                (" Level Up! ", "white"),
                (name, get_colour_for_type("resource")),
                (" - Level ", "white"),
                (str(level), "number")
            ])
        self.sound_manager.queue("level_up_mastery")

    def _log_rare_drop(self, item_id, item, tier, magic_find):
        if tier not in ("rare", "epic", "legendary", "mythic"):
            return

        colour = get_rarity_colour(tier)
        fmt = get_stat_format("magic_find")
        formatted = fmt(magic_find)
        label = get_stat_display_name("magic_find")

        self.message_log.queue([
            (f"{tier.upper()} DROP! ", colour),
            (item.get("name", item_id).title(), colour),
            (" (+", "white"),
            (f"{formatted} ", "number"),
            (label, get_stat_colour("magic_find")),
            (")", "white"),
        ])
        self.sound_manager.queue("drop")

    def handle_xp_result(self, result):
        for skill, amount in result.final_xp.items():
            self.handle_gainxp(skill, amount, origin=self.player.rect.center)

    def handle_drop_result(self, result, final_magic_find=0):
        for dropset in [result.final_drops]:
            for item_id, item_data in dropset.items():
                qty = item_data.get("qty", 1)
                tier = item_data.get("tier", "mythic")
                scaled_chance = item_data.get("chance", 0)

                contribution = get_mastery_contribution_for_item(item_id)
                affected_ids = set([item_id]) | set(contribution.keys())

                base_id = self.player.inventory.get_base_id(item_id)
                item = ITEMS.get(base_id, {})
                item_name = item.get("name", "UNKNOWN")

                if item_id not in self.player.discovered_resources:
                    self.player.discovered_resources.add(item_id)
                    self.message_log.queue([
                        ("Discovered Resource: ", "white"),
                        (item_name, get_colour_for_type("mastery"))
                    ])

                prev_levels = {
                    res_id: self.player.mastery.get_resource_mastery_level(res_id)[0]
                    for res_id in affected_ids
                }

                self.player.inventory.add_item(item_id, qty)
                self.tasks.handle_resource_gain(item_id, qty)

                self._log_rare_drop(item_id, item, tier, final_magic_find)

                self.pickup_log.log(item_id, qty)

                for res_id in affected_ids:
                    new_level = self.player.mastery.get_resource_mastery_level(res_id)[0]
                    prev_level = prev_levels[res_id]
                    if new_level > prev_level:
                        self._log_mastery_level_up(res_id, ITEMS.get(res_id, {}), new_level, prev_level)
                        self.player.mastery.check_total_mastery_rewards(self.message_log)

    def handle_enemy_result(self, result):
        enemy = result.target
        if not enemy:
            return

        self.damage_popups.append(Popup(enemy.pos.x, enemy.pos.y, enemy.combat.last_damage_taken))

        if enemy.sounds.get("hit"):
            self.sound_manager.queue(enemy.sounds["hit"])

        if not result.final_hit:
            return
        
        self.sound_manager.queue("enemy_death")
        final_mf = self.player.stats.get_total_stats_with_enemy_bonus(enemy).get("magic_find", 0)
        result.final_drops = enemy.drop_items(final_mf)
        self.handle_drop_result(result, final_mf)

        self.handle_xp_result(result)
        
        if enemy.id not in self.player.discovered_enemies:
            self.player.discovered_enemies.add(enemy.id)
            self.message_log.queue([
                ("Discovered Enemy: ", "white"),
                (enemy.name, get_colour_for_type("enemy"))
            ])

        prev = self.player.beastiary.get_enemy_kill_count(enemy.id)
        new = prev + 1
        self.player.beastiary.update_enemy_kill_count(enemy.id, new)

        prev_level, _ = get_beastiary_progress(enemy.id, prev)
        new_level, _ = get_beastiary_progress(enemy.id, new)

        if new_level > prev_level:
            self.message_log.queue([
                ("Beastiary", get_colour_for_type("beastiary")),
                (" Level Up! ", "white"),
                (enemy.name, get_colour_for_type("enemy")),
                (" - Level ", "white"),
                (str(new_level), "number")
            ])
            self.sound_manager.queue("level_up_beastiary")

        self.player.beastiary.check_total_beastiary_rewards(self.handle_gainxp, self.message_log)
        self.tasks.handle_kill(enemy.id)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                self.handle_keydown_event(event.key)

            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL):
                self.handle_mouse_event(event)

    def update(self, dt, clock):
        clear_tooltips()

        self.mouse_pos = pygame.mouse.get_pos()
        self.mouse_world = pygame.Vector2(self.mouse_pos) - self.camera.offset

        if self.state != GameState.PLAYING:
            return
        
        mouse_just_clicked = self.mouse_held and not self._mouse_prev_held
        self._mouse_prev_held = self.mouse_held

        self.hovered_target, self.target_pos, self.target_radius = self.player.get_target_info(
            self.current_zone, self.mouse_world, self.player.active_item.skill
        )

        self.player.freeze = not self.camera.is_following()
        self.player.update(dt, self.current_zone.size)

        if self.player.combat.hp <= 0:
            self.player.combat.revive()
            self._change_zone(self.player.last_safe_zone_id)

        if self.player.combat.just_took_damage:
            self.damage_overlay_alpha = 100
            self.player.combat.just_took_damage = False

        if self.damage_overlay_alpha > 0:
            self.damage_overlay_alpha -= self.damage_overlay_decay_rate * dt
            self.damage_overlay_alpha = max(0, self.damage_overlay_alpha)

        self.camera.update(dt, self.player.rect)

        if not self.state == GameState.PAUSED:
            self.current_zone.update(dt, self.player, self.camera, self.sound_manager)

        self.handle_zone_transition(dt)

        item = self.player.active_item

        should_use = False
        if item.skill != "combat":
            should_use = self.mouse_held and item.ready(self.player)
        else:
            should_use = mouse_just_clicked and item.ready(self.player)

        if should_use and self.hovered_target:
            if item.skill == "combat":
                item.trigger(self.player)  # Trigger cooldown manually
                self.current_zone.process_combat(self.player, self.hovered_target, item, self.camera, dt)
            else:
                item.use(self.player, self.current_zone, self.camera, self.sound_manager.queue, dt, self.hovered_target, self.tasks.handle_node_gather)
#



# TOOLS ARE NOW BROKEN TOOLS ARE NOW BROKEN TOOLS ARE NOW BROKEN TOOLS ARE NOW BROKEN TOOLS ARE NOW BROKEN TOOLS ARE NOW BROKEN TOOLS ARE NOW BROKEN 



#
        self.current_zone.flush_combat_results(self)
        
        self.pickup_log.update()

        for popup in self.damage_popups:
            popup.update()

        for popup in self.xp_popups:
            popup.update()

        self.damage_popups = [p for p in self.damage_popups if p.is_alive()]
        self.xp_popups = [p for p in self.xp_popups if p.is_alive()]

        unclaimed_count = sum(1 for t in self.tasks.tasks if t.ready_to_claim and not t.completed)
        
        self._unclaimed_reminder_timer += dt

        if unclaimed_count > 0:
            if not self._notified_unclaimed or self._unclaimed_reminder_timer >= 30:
                self.message_log.queue([
                    ("You have ", "white"),
                    (str(unclaimed_count), (100, 255, 100)),
                    (" unclaimed task(s)! Press T to open Tasks.", "white")
                ])
                self._notified_unclaimed = True
                self._unclaimed_reminder_timer = 0
        else:
            self._notified_unclaimed = False
            self._unclaimed_reminder_timer = 0

        self._popup_offsets = {}

        self.fps = clock.get_fps()

    def draw_hotbar_slot(self, screen, x, y, index, item_id, selected):
        rect = pygame.Rect(x, y, HOTBAR_EQUIP_SLOT_SIZE, HOTBAR_EQUIP_SLOT_SIZE)

        slot_colour = HOTBAR_EQUIP_SLOT_SELECTED_COLOUR if selected else HOTBAR_EQUIP_SLOT_EMPTY_COLOUR
        pygame.draw.rect(screen, slot_colour, rect)
        pygame.draw.rect(screen, HOTBAR_EQUIP_PANEL_BORDER_COLOUR, rect, HOTBAR_EQUIP_PANEL_BORDER_WIDTH)

        number_label = self.font.render(str(index), True, HOTBAR_EQUIP_LABEL_COLOUR)
        screen.blit(number_label, (x, y + HOTBAR_EQUIP_SLOT_SIZE + HOTBAR_EQUIP_LABEL_Y_SPACING))

        if item_id:
            item = self.player.inventory.get_item_full_data(item_id)
            label = self.get_item_type_label(item.base_data)

            if label:
                label_surf = self.font.render(label, True, (255, 255, 255))
                screen.blit(label_surf, (
                    rect.right - label_surf.get_width() - 4,
                    rect.bottom - label_surf.get_height() - 4
                ))

            # Tooltip
            if rect.collidepoint(self.mouse_pos):
                queue_tooltip({
                    "type": "item",
                    "data": item,
                    "position": (self.mouse_pos[0] + 16, self.mouse_pos[1] + 16),
                    "required_states": {GameState.PLAYING, GameState.INVENTORY},
                })

    def get_item_type_label(self, item):
        skill = item.get("skill", None)
        if skill != "combat":
            return "T"
        elif skill == "combat":
            return "W"
        return "?"
    
    def draw_hotbar(self, screen):
        x, y = HOTBAR_X, HOTBAR_Y
        spacing = HOTBAR_EQUIP_SLOT_SIZE + HOTBAR_EQUIP_SLOT_SPACING

        for i, item_id in enumerate(self.player.inventory.hotbar):
            is_selected = (i == self.player.inventory.selected_hotbar_index)
            self.draw_hotbar_slot(screen, x, y, i + 1, item_id, is_selected)
            x += spacing

    def _draw_hp_bar(self, screen, x, y, width, height):
        hp = min(self.player.combat.hp, self.player.stats.total_stats.get("max_hp", 1))
        max_hp = self.player.stats.total_stats.get("max_hp", 1)
        progress = hp / max_hp if max_hp else 0
        text = f"HP: {int(hp)}/{int(max_hp)}"

        hp_bar_rect = pygame.Rect(x, y, width, height)
        draw_progress_bar(screen, hp_bar_rect, progress, (255, 80, 80), text=text, font=self.font)

        mouse_pos = pygame.mouse.get_pos()
        if hp_bar_rect.collidepoint(mouse_pos):
            healing_sources = self.player.stats.get_healing_sources()

            queue_tooltip({
                "type": "hp_healing_sources",
                "data": {
                    "name": "Sources of Healing",
                    "healing_sources": healing_sources,
                },
                "position": mouse_pos,
                "required_states": {GameState.PLAYING},
            })

    def _draw_skill_bars(self, screen, x, y, width, height, spacing):
        for skill, level, xp_in, xp_needed in self.player.skills.get_skill_progress():
            progress = xp_in / xp_needed if xp_needed else 0
            colour = SKILL_COLOURS.get(skill, (200, 200, 200))
            label = f"{skill.capitalize()} Lv {level} ({xp_in}/{xp_needed})"

            bar_rect = pygame.Rect(x, y, width, height)
            draw_progress_bar(screen, bar_rect, progress, colour, text=label, font=self.font)

            if bar_rect.collidepoint(self.mouse_pos):
                self._queue_skill_tooltip(skill)

            y += height + spacing

        return y

    def _draw_gold_and_action(self, screen, x, y):
        gold = self.font.render(f"Gold: {self.player.gold}", True, UI_GOLD_TEXT_COLOUR)
        screen.blit(gold, (x, y))
        y += gold.get_height() + 4

        action = self.player.active_item.action.title()
        colour = SKILL_COLOURS.get(action.lower(), (255, 255, 255))
        action_surf = self.font.render(f"Action: {action}", True, colour)
        screen.blit(action_surf, (x, y))
        y += action_surf.get_height() + 4

        return y

    def _queue_skill_tooltip(self, skill):
        level = self.player.skills.get_skill_level(skill)
        total_xp = self.player.skills.get_skill_total_xp(skill)

        bonus_info = self.player.stats.level_up_bonuses.get(skill, {})
        stat = bonus_info.get("stat")
        per_level = bonus_info.get("per_level", 0)
        desc = describe_stat_bonus(stat, level * per_level)

        tooltip_data = {
            "type": "skill",
            "data": {
                "xp": total_xp,
                "bonus": {
                    "label": desc["label"],
                    "text": desc["formatted"],
                    "colour": desc["colour"]
                },
                "eta_next": format_time_hours(self.player.skills.time_until_level_up(skill, level + 1)),
                "eta_60": format_time_hours(self.player.skills.time_until_level_up(skill, 60)),
                "xp_rate": format_number_short(self.player.skills.xp_per_hour(skill)),
            },
            "position": (self.mouse_pos[0] + 16, self.mouse_pos[1] + 16),
            "required_states": {GameState.PLAYING},
        }

        queue_tooltip(tooltip_data)

    def draw_ui(self, screen):
        panel_x = VIEWPORT_WIDTH + UI_X_OFFSET
        panel_y = UI_TEXT_START_Y
        bar_width = UI_PANE_WIDTH - 2 * UI_X_OFFSET
        bar_height = 20
        bar_spacing = 12

        self._draw_hp_bar(screen, panel_x, panel_y, bar_width, bar_height)
        panel_y += bar_height + bar_spacing

        panel_y = self._draw_skill_bars(screen, panel_x, panel_y, bar_width, bar_height, bar_spacing)
        panel_y = self._draw_gold_and_action(screen, panel_x, panel_y)

        if self.state == GameState.MESSAGE_LOG:
            self.message_log.draw_scrollable(screen)
        else:
            self.message_log.draw_floating(screen)

        self.pickup_log.draw(screen, panel_x, SCREEN_HEIGHT - 50)

    def draw_all_ui(self, screen):
        pygame.draw.rect(screen, UI_PANE_COLOUR, (VIEWPORT_WIDTH, 0, UI_PANE_WIDTH, SCREEN_HEIGHT))
        self.draw_ui(screen)
        self.draw_hotbar(screen)

        active_ui = self.get_active_ui()
        if active_ui:
            active_ui.update()
            active_ui.draw(screen)

        for tooltip in get_tooltips():
            if self.state in tooltip.get("required_states", {}):
                tooltip_ctx = TooltipContext(font=self.font, player=self.player, **tooltip)
                lines = build_tooltip_lines(tooltip, tooltip_ctx)
                draw_tooltip_lines(screen, lines, tooltip_ctx.font, tooltip["position"])

    def _is_paused(self):
        return self.state not in (GameState.PLAYING, GameState.MESSAGE_LOG)
    
    def _draw_zone(self):
        self.current_zone.draw(self.surface, self.camera, self.font, self.player, self.zones, self.sound_manager)

    def _draw_player(self):
        pygame.draw.rect(self.surface, PLAYER_RECT_COLOUR, self.camera.apply(self.player.rect))

    def _draw_attack_radius(self):
        if self.player.active_item:
            self.player.draw_attack_cooldown(self.surface, self.camera)

    def _draw_popups(self):
        for popup in self.damage_popups + self.xp_popups:
            popup.draw(self.surface, self.camera, self.font)

    def _draw_damage_overlay(self):
        if self.damage_overlay_alpha <= 0:
            return

        overlay = pygame.Surface((VIEWPORT_WIDTH, VIEWPORT_HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 0, 0, int(self.damage_overlay_alpha)))
        self.surface.blit(overlay, (0, 0))

    def _draw_zone_title(self, screen):
        boss_title = self.camera.boss_title
        boss_subtitle = self.camera.boss_subtitle
        boss_title_alpha = self.camera.boss_title_alpha

        if boss_title and boss_title_alpha> 0:
            title_surf = self.camera.boss_font.render(boss_title, True, (255, 255, 255))
            subtitle_surf = self.camera.boss_subfont.render(boss_subtitle, True, (200, 200, 200))

            title_surf.set_alpha(boss_title_alpha)
            subtitle_surf.set_alpha(boss_title_alpha)

            screen.blit(
                title_surf,
                (self.camera.viewport_width // 2 - title_surf.get_width() // 2, self.camera.viewport_height // 3)
            )
            screen.blit(
                subtitle_surf,
                (self.camera.viewport_width // 2 - subtitle_surf.get_width() // 2, self.camera.viewport_height // 3 + 48)
            )

    def _draw_pause_overlay(self, screen):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, 0))

        text_string = "PAUSED"
        text_colour = (255, 255, 255)
        text_surface = self.font.render(text_string, True, text_colour)

        screen.blit(
            text_surface,
            (
                VIEWPORT_WIDTH // 2 - text_surface.get_width() // 2,
                VIEWPORT_HEIGHT // 2 - text_surface.get_height() // 2
            )
        )

    def _draw_ui(self, screen):
        self.draw_all_ui(screen)

    def _draw_fps(self, screen):
        fps = self.fps if hasattr(self, 'fps') else 0
        text_surface = self.font.render(f"{int(fps)} FPS", True, (200, 200, 200))

        screen.blit(
            text_surface,
            (
                SCREEN_WIDTH - text_surface.get_width() - 10,
                SCREEN_HEIGHT - 20
            )
        )

    def draw(self, screen):
        screen.fill((0, 0, 0))

        self.surface.fill((20, 20, 20))

        self._draw_zone()
        self._draw_player()
        self._draw_attack_radius()
        self._draw_popups()
        self._draw_damage_overlay()

        screen.blit(self.surface, (0, 0))

        self.player.draw_targeting_overlay(screen, self.camera, self.hovered_target, self.target_pos, self.target_radius)

        self._draw_zone_title(screen)

        if self._is_paused():
            self._draw_pause_overlay(screen)

        self.transition.draw(screen)

        self._draw_ui(screen)

        self._draw_fps(screen)

        self.sound_manager.flush()