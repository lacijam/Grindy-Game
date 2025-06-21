import pygame
import random

from resourcenode import ResourceNode
from resource_node_data import *
from constants import *
from utils import *
from tooltip_builder import *
from enemy_classes import ENEMY_CLASSES
from enemy import EnemyContext
from particle import Particle
from gamestate import GameState
from utils import calculate_shake_intensity
from ability_effects_data import ABILITY_EFFECTS_DATA
from counter_data import COUNTER_DATA

class Zone:
    def __init__(self, id, size, safe=True, num_enemies=0, enemy_spawn_table=[], num_resources=0, 
                 resource_node_spawn_table=[], connections=None, name="", 
                 type="combat", requirements=None):
        self.id = id
        self.size = size
        self.safe = safe
        self.num_enemies = num_enemies
        self.enemy_spawn_table = enemy_spawn_table
        self.num_resources = num_resources
        self.resource_node_spawn_table = resource_node_spawn_table
        self.connections = connections or {}
        self.name = name
        self.type = type
        self.requirements = requirements

        self.enemies = []
        self.pending_enemy_results = []

        self.resource_nodes = []
        self.nodes_to_kill = []

        self.boss = None

        self.kill_counts = {}

        self.prepared = False
        self.has_intro_played = False

        self.particles = []

        self.effect_hooks = []

    def prepare(self, player):
        if self.prepared:
            return
        
        self.prepared = True
        self.spawn_initial_enemies(player)
        self.spawn_resources()
        self.create_portals()

    def get_entry_point(self, exit_direction, margin=50):
        reverse = {
            "left": "right",
            "right": "left",
            "top": "bottom",
            "bottom": "top"
        }
        enter_direction = reverse.get(exit_direction)

        mid = self.size // 2
        if enter_direction == "left":
            return margin, mid
        elif enter_direction == "right":
            return self.size - margin, mid
        elif enter_direction == "top":
            return mid, margin
        elif enter_direction == "bottom":
            return mid, self.size - margin
        else:
            return mid, mid  # Center fallback

    def spawn_particles(self, x, y, colour, source_x, source_y, count, life_min, life_max, dt):
        for _ in range(count):
            self.particles.append(Particle(x, y, colour, source_x or x, source_y or y, life_min, life_max, dt))

    def create_portals(self):
        margin = 16  
        width = 32  
        self.portals = {}

        if "left" in self.connections:
            self.portals["left"] = pygame.Rect(0, self.size // 2 - width // 2, margin, width)
        if "right" in self.connections:
            self.portals["right"] = pygame.Rect(self.size - margin, self.size // 2 - width // 2, margin, width)
        if "top" in self.connections:
            self.portals["top"] = pygame.Rect(self.size // 2 - width // 2, 0, width, margin)
        if "bottom" in self.connections:
            self.portals["bottom"] = pygame.Rect(self.size // 2 - width // 2, self.size - margin, width, margin)

    def player_meets_requirements(self, player):
        for skill, required_level in self.requirements.items():
            level = player.skills.get_skill_level(skill)
            if level < required_level:
                return False
        return True

    def choose_enemy_type(self):
        total = sum(weight for _, weight in self.enemy_spawn_table)
        r = random.uniform(0, total)
        accum = 0
        for enemy_class, weight in self.enemy_spawn_table:
            accum += weight
            if r <= accum:
                return enemy_class
            
        return self.enemy_spawn_table[0][0] # fallback

    def spawn_enemy(self, player):
        x = random.randint(0, self.size - 20)
        y = random.randint(0, self.size - 20)
        enemy_id = self.choose_enemy_type()
        enemy_class = ENEMY_CLASSES[enemy_id]
        enemy = enemy_class(x, y, player, self)
        if enemy.type == "boss":
            self.boss = enemy

        return enemy

    def spawn_initial_enemies(self, player):
        for _ in range(self.num_enemies):
            enemy = self.spawn_enemy(player)
            self.enemies.append(enemy)

    def get_boss_metadata(self):
        if not self.boss:
            return None, None, None  # rect, name, subtitle

        data = ENEMY_DATA.get(self.boss.id, {})
        name = data.get("name", self.boss.id).title()
        subtitle = data.get("subtitle", "")  # Add 'subtitle' support to enemy_data
        return self.boss.rect, name, subtitle

    def choose_resource_node_type(self):
        total = sum(w for _, w in self.resource_node_spawn_table)
        r = random.uniform(0, total)
        accum = 0
        for id, weight in self.resource_node_spawn_table:
            accum += weight
            if r <= accum:
                return id
        return self.resource_node_spawn_table[0][0]  # fallback
    
    def spawn_resources(self):
        for _ in range(self.num_resources):
            x = random.randint(0, self.size - 20)
            y = random.randint(0, self.size - 20)
            node_id = self.choose_resource_node_type()
            node = ResourceNode(x, y, node_id)
            self.resource_nodes.append(node)

    def check_portal_trigger(self, player, zones_by_id):
        for direction, rect in self.portals.items():
            if player.rect.colliderect(rect):
                target_zone_id = self.connections.get(direction)
                target_zone = zones_by_id.get(target_zone_id)

                if not target_zone:
                    continue

                if not target_zone.player_meets_requirements(player):
                    return None, None
                
                return target_zone_id, direction
        return None, None

    def _calculate_damage(self, context):
        strength_multiplier = 1 + context["strength"] / 100
        damage = context["base_damage"] * strength_multiplier

        crit = False
        if context["crit_chance"] > 0:
            if random.random() < context["crit_chance"] / 100:
                damage *= 1 + context["crit_damage"] / 100
                crit = True

        return damage, crit

    def _calculate_knockback_vector(self, player, target, knockback):
        direction = pygame.Vector2(target.rect.center) - pygame.Vector2(player.rect.center)
        return direction.normalize() * knockback if direction.length_squared() > 0 else pygame.Vector2(0, 0)

    def _spawn_combat_effects(self, camera, player, target, damage, crit, dt):
        if camera:
            camera.shake(calculate_shake_intensity(damage, crit), duration=0.2)

        self.spawn_particles(
            x=target.rect.centerx,
            y=target.rect.centery,
            colour=(180, 0, 0),
            source_x=player.pos.x,
            source_y=player.pos.y,
            count=10,
            life_min=0.2,
            life_max=0.3,
            dt=dt
        )


    def process_combat(self, player, target, item, camera, dt):
        context = {
            "player": player,
            "target": target,
            "base_damage": item.damage,
            "strength": player.stats.total_stats.get("strength", 0),
            "crit_chance": player.stats.total_stats.get("crit_chance", 0),
            "crit_damage": player.stats.total_stats.get("crit_damage", 0),
            "magic_find": 0,
            "is_first_hit": not getattr(target, "was_hit", False),
            "damage": 0,
            "effect_hooks": [],
            "zone": self,
            "dt": dt,
            "mouse_pos": pygame.mouse.get_pos(),
        }

        player.combat.apply_combat_phase("pre_damage", context)
        player.combat.apply_combat_phase("pre_strength", context)
        player.combat.apply_combat_phase("pre_crit", context)

        damage, crit = self._calculate_damage(context)
        context["damage"] = damage
        context["crit"] = crit

        player.combat.apply_combat_phase("post_crit", context)

        final_damage = int(round(context["damage"]))
        direction = self._calculate_knockback_vector(player, target, item.knockback)

        result = target.combat.take_damage(final_damage, direction, player, "weapon")
        self.pending_enemy_results.append(result)

        context["damage"] = final_damage
        player.combat.apply_combat_phase("post_damage", context)
        self.effect_hooks.extend(context.get("effect_hooks", []))

        self._spawn_combat_effects(camera, player, target, final_damage, result.final_hit, dt)

        if result.final_hit:
            player.combat.apply_combat_phase("on_kill", context)

    def flush_combat_results(self, game):
        if not self.pending_enemy_results:
            return

        for result in self.pending_enemy_results:
            game.handle_enemy_result(result)

            player = result.attacker # Update weapon counter if present.
            if result.final_hit and player and player == game.player:
                active_item_id = player.active_item_id
                metadata = player.get_active_item_instance_metadata()
                base_id = player.inventory.get_base_id(active_item_id)
                base_data = ITEMS.get(base_id, {})
                counter_id = base_data.get("counter_id")
                counter_data = COUNTER_DATA.get(counter_id)

                if counter_data:
                    valid_sources = player.get_active_item_effect_sources()
                    valid_sources.add("weapon")
                    if result.reason in valid_sources:
                        counter_type = counter_data.get("type")
                        counters = metadata.setdefault("counters", {})
                        if counter_type == "kills":
                            counters["kills"] = counters.get("kills", 0) + 1
                        elif counter_type == "xp":
                            counters["xp"] = counters.get("xp", 0) + result.final_xp.get("combat", 0)
                        player.update_active_item_metadata(metadata)

            if result.final_hit:
                self.enemies.remove(result.target)
                self.enemies.append(self.spawn_enemy(result.attacker))

        self.pending_enemy_results.clear()

    def update(self, dt, player, camera, sound_manager):
        now = pygame.time.get_ticks()

        self.effect_hooks = [
            hook for hook in self.effect_hooks
            if now - hook["start_time"] < ABILITY_EFFECTS_DATA.get(hook["type"], {}).get("duration", 1000)
        ]

        ctx = EnemyContext(self, player, camera, self.size)
        ctx.sound_manager = sound_manager

        for enemy in self.enemies:
            enemy.update(dt, ctx)

        for resource_node in self.resource_nodes:
            resource_node.update(dt)

        for node in self.nodes_to_kill:
            if node in self.resource_nodes:
                new_node_id = self.choose_resource_node_type()
                new_node = ResourceNode(
                    random.randint(0, self.size - 20),
                    random.randint(0, self.size - 20),
                    new_node_id
                )

                self.resource_nodes.remove(node)
                self.resource_nodes.append(new_node)

        self.nodes_to_kill.clear()

        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if not p.is_dead()]

    def draw_portals(self, surface, camera, font, player, zones_by_id):
        mouse_pos = pygame.mouse.get_pos()
        
        for direction, rect in self.portals.items():
            # Get target zone
            target_zone_id = self.connections.get(direction)
            target_zone = zones_by_id.get(target_zone_id)

            if not target_zone:
                continue

            screen_rect = camera.apply(rect)

            locked = not target_zone.player_meets_requirements(player) if target_zone else False
            colour = (255, 0, 0) if locked else (255, 255, 0)

            # draw the portal
            pygame.draw.rect(surface, colour, screen_rect, 2)

            # mask with red tint if locked
            if locked:
                overlay = pygame.Surface(screen_rect.size, pygame.SRCALPHA)
                overlay.fill((255, 0, 0, 100))
                surface.blit(overlay, screen_rect.topleft)

            if screen_rect.collidepoint(mouse_pos):
                queue_tooltip({
                    "type": "portal",
                    "data": {
                        "name": target_zone.name,
                        "requirements": target_zone.requirements or {}
                    },
                    "position": mouse_pos,
                    "required_states": {GameState.PLAYING}
                })

    def queue_effect(self, effect_id, extra_data):
        hook = {
            "type": effect_id,
            "start_time": pygame.time.get_ticks(),
        }
        if extra_data:
            hook.update(extra_data)
        self.effect_hooks.append(hook)


    def render_effect_hooks(self, screen, camera, font, player, sound_manager):
        # Draw fiery ring around player if phoenix_aura is active
        has_phoenix_aura = any(
            effect["id"] == "phoenix_aura"
            for effect in player.stats.active_effects
        )

        if has_phoenix_aura:
            player_pos = camera.reverse(player.rect.center)
            # Flicker radius slightly for visual effect
            base_radius = 110
            radius_variation = random.randint(-3, 3)
            radius = base_radius + radius_variation

            # Flicker alpha slightly
            alpha = random.randint(100, 200)

            # Create surface for the ring
            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 120, 0, alpha), (radius, radius), radius, width=4)

            # Blit centered on player
            rect = surf.get_rect(center=player_pos)
            screen.blit(surf, rect.topleft)

        for hook in self.effect_hooks:
            effect_id = hook["type"]
            data = ABILITY_EFFECTS_DATA.get(effect_id)
            if not data:
                continue

            sound = data.get("sound")
            if sound and not hook.get("sound_played"):
                sound_manager.queue(sound)
                hook["sound_played"] = True

            extra_data = data.get("extra_data", {})

            if effect_id == "chain_lightning":
                from_pos = camera.reverse(hook["from_pos"])
                to_pos = camera.reverse(hook["to_pos"])
                colour = extra_data.get("colour", (255, 255, 255))
                jitter_lines = extra_data.get("jitter_lines", 3)

                for _ in range(jitter_lines):
                    offset_x = random.randint(-3, 3)
                    offset_y = random.randint(-3, 3)
                    pygame.draw.line(
                        screen,
                        colour,
                        (from_pos[0] + offset_x, from_pos[1] + offset_y),
                        (to_pos[0] + offset_x, to_pos[1] + offset_y),
                        2
                    )

            elif effect_id == "phoenix_aura_hit":
                x, y = hook["x"], hook["y"]
                colour = extra_data.get("colour", (255, 100, 0))
                count = extra_data.get("particle_count", 1)
                life_min = extra_data.get("life_min", 0.1)
                life_max = extra_data.get("life_max", 0.2)

                self.spawn_particles(
                    x=x,
                    y=y,
                    colour=colour,
                    source_x=None,
                    source_y=None,
                    count=count,
                    life_min=life_min,
                    life_max=life_max,
                    dt=0.016
                )

            elif effect_id == "cleave":
                x, y = hook["x"], hook["y"]
                radius = ABILITY_DATA.get("cleave", {}).get("values", {}).get("radius", 100)

                # Flickering red ring
                base_colour = (200, 0, 0)
                alpha = random.randint(120, 200)
                flicker = random.randint(-3, 3)
                radius += flicker

                surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (*base_colour, alpha), (radius, radius), radius, width=2)

                screen.blit(surf, camera.apply(pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)).topleft)
                
            elif effect_id == "cleave_hit":
                x, y = hook["x"], hook["y"]
                colour = extra_data.get("colour", (200, 0, 0))
                count = extra_data.get("particle_count", 8)
                life_min = extra_data.get("life_min", 0.1)
                life_max = extra_data.get("life_max", 0.2)

                self.spawn_particles(
                    x=x, y=y, colour=colour,
                    source_x=None, source_y=None,
                    count=count,
                    life_min=life_min,
                    life_max=life_max,
                    dt=0.016
                )


    def draw(self, screen, camera, font, player, zones_by_id, sound_manager):
        # Zone background and border
        zone_rect = pygame.Rect(0, 0, self.size, self.size)
        pygame.draw.rect(screen, (50, 50, 50), camera.apply(zone_rect))  # fill
        pygame.draw.rect(screen, (200, 50, 50), camera.apply(zone_rect), 4)  # border

        for enemy in self.enemies:
            enemy.draw(screen, camera, font)

            # Check mouse over
            if camera.apply(enemy.rect).collidepoint(pygame.mouse.get_pos()):
                queue_tooltip({
                    "type": "enemy",
                    "data": {
                        "enemy_label": [enemy.level, enemy.name],
                        "hp": enemy.combat.hp,
                        "drop_table": enemy.drop_table
                    },
                    "position": pygame.mouse.get_pos(),
                    "required_states": {GameState.PLAYING}
                })

            # Draw name + level label
            enemy_screen_rect = camera.apply(enemy.rect)
            label_text = f"[Lv. {enemy.level}] {enemy.name}"

            # Distance from player (in pixels)
            dist = player.distance_to(enemy)

            # Set fade distance range (adjust as needed)
            max_dist = 300
            if dist > max_dist:
                continue
            
            min_alpha = 0  # lowest alpha
            alpha = max(min_alpha, 255 - int((dist / max_dist) * 255))

            # Colour based on level diff
            player_level = player.skills.get_skill_level("combat")
            colour = get_enemy_level_colour(enemy.level, player_level)

            # Create label surface with alpha
            font_surf = font.render(label_text, True, colour)
            font_surf.set_alpha(alpha)

            # Position above enemy
            label_x = enemy_screen_rect.centerx - font_surf.get_width() // 2
            label_y = enemy_screen_rect.top - font_surf.get_height() - 4
            screen.blit(font_surf, (label_x, label_y))

        self.draw_portals(screen, camera, font, player, zones_by_id)

        for resource_node in self.resource_nodes:
            resource_node.draw(screen, camera, font, player)
            if camera.apply(resource_node.rect).collidepoint(pygame.mouse.get_pos()):
                queue_tooltip({
                    "type": "resource_node",
                    "data": {
                        "id": resource_node.id,
                        "name": resource_node.data.get("name", resource_node.id).title(),
                        "reward_xp": resource_node.reward_xp,
                        "required_skills": resource_node.required_skills,
                        "drop_table": resource_node.data.get("drop_table", [])
                    },
                    "position": pygame.mouse.get_pos(),
                    "required_states": {GameState.PLAYING}
                })

        for p in self.particles:
            p.draw(screen, camera)

        self.render_effect_hooks(screen, camera, font, player, sound_manager)