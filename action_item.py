import pygame
import random

from utils import calculate_shake_intensity, UseResult
from resourcenode import ResourceNode

class ActionItem:
    def __init__(self, id, radius, delay, damage, knockback=300, skill="combat"):
        self.id = id
        self.radius = radius
        self.delay = delay
        self.damage = damage
        self.knockback = knockback
        self.skill = skill
        self._last_used = 0

    @property
    def action(self):
        return self.skill

    def get_cooldown_progress(self, player):
        last = player.item_cooldowns.get(self.id, 0)
        attack_speed = player.stats.total_stats.get("attack_speed", 0)
        multiplier = 1 + attack_speed / 100
        effective_delay = self.delay / multiplier
        elapsed = pygame.time.get_ticks() - last
        return min(elapsed / effective_delay, 1.0)

    def use(self, player, zone, camera, play_sound_fn, dt, target, on_node_gather=None):
        if not self.ready(player):
            return None

        self.trigger(player)

        if self.skill != "combat":
            return self._use_on_resource_node(player, zone, play_sound_fn, target, on_node_gather)

        return None


    def _use_on_resource_node(self, player, zone, play_sound_fn, target, on_node_gather=None):
        if not isinstance(target, ResourceNode):
            return None

        if not target.skill or target.skill != self.skill:
            return None

        if player.skills.get_skill_level(target.skill) < target.required_skills.get(target.skill, 0):
            return None

        damage = 1

        partial_xp = target.get_partial_xp(damage)
        partial_drops = target.get_partial_drops(damage)

        self.trigger(player)

        depleted = target.mine(damage)

        if on_node_gather:
            on_node_gather(target.id, amount=1)

        if play_sound_fn:
            play_sound_fn(f"{target.skill}_strike")

        result = UseResult()
        result.partial_xp[target.skill] = partial_xp
        result.partial_drops = partial_drops

        if depleted:
            zone.nodes_to_kill.append(target)

            if play_sound_fn:
                play_sound_fn("enemy_death")

            result.final_hit = True
            result.partial_xp = {}
            result.final_xp[target.skill] = target.reward_xp
            result.final_magic_find = 0
            result.final_drops = target.drop_items()

        return result

    def _calculate_knockback_direction(self, player, target):
        direction = pygame.Vector2(target.rect.center) - pygame.Vector2(player.rect.center)
        if direction.length_squared() > 0:
            return direction.normalize() * self.knockback
        else:
            return pygame.Vector2(0, 0)

    def _build_combat_context(self, player, target):
        return {
            "player": player,
            "target": target,
            "base_damage": self.damage,
            "strength": player.stats.total_stats["strength"],
            "crit_chance": player.stats.total_stats["crit_chance"],
            "crit_damage": player.stats.total_stats["crit_damage"],
            "magic_find": 0,
            "is_first_hit": not target.was_hit,
            "damage": 0,
            "effect_hooks": []
        }

    def _calculate_damage(self, context):
        strength_multiplier = 1 + context["strength"] / 100
        damage = context["base_damage"] * strength_multiplier

        crit = False
        if context["crit_chance"] > 0:
            if random.random() < context["crit_chance"] / 100:
                damage *= 1 + context["crit_damage"] / 100
                crit = True

        return damage, crit

    def ready(self, player):
        last = player.item_cooldowns.get(self.id, 0)
        attack_speed = player.stats.total_stats.get("attack_speed", 0)
        multiplier = 1 + attack_speed / 100
        effective_delay = self.delay / multiplier

        return pygame.time.get_ticks() - last >= effective_delay
    
    def trigger(self, player):
        self._last_used = pygame.time.get_ticks()
        player.item_cooldowns[self.id] = self._last_used

    @property
    def action(self):
        return "combat"