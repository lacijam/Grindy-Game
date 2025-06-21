import pygame

from constants import *
from action_item import ActionItem
from beastiary_tracker import BeastiaryTracker
from resource_mastery_tracker import ResourceMasteryTracker
from player_skills import PlayerSkills
from player_stats import PlayerStats
from player_equipment import PlayerEquipment
from player_inventory import PlayerInventory
from combat_entity import CombatEntity
from base_entity import BaseEntity
from ability_data import ABILITY_DATA
from enchantment_data import ENCHANTMENT_DATA
from item_data import ITEMS

class Player(BaseEntity):
    def __init__(self, x, y, size, zone):
        super().__init__("player", x, y, size, size, zone, type="player")

        self.base_speed = 150

        self.gold = 0
        self.freeze = False

        self.fist = ActionItem(
            "fist",
            radius=40,
            delay=800,
            damage=5,
            skill="combat",
        )

        self.active_item = self.fist
        self.active_item_id = None
        self.active_item_metadata = {}

        self.equipment = PlayerEquipment(self)
        self.inventory = PlayerInventory(self)

        self.skills = PlayerSkills(self)
        self.stats = PlayerStats(self)

        self.beastiary = BeastiaryTracker(self)
        self.mastery = ResourceMasteryTracker(self)

        self.combat = CombatEntity(
            owner=self,
            hp=self.stats.total_stats["max_hp"],
            max_hp=self.stats.total_stats["max_hp"],
            max_hp_getter=lambda: self.stats.total_stats.get("max_hp", 0),
            weight=1.0,
            regen_rate_getter=lambda: self.stats.total_stats.get("vitality", 0),
            regen_interval=1000,
            damage_reduction_fn=lambda: self.stats.calculate_damage_reduction(),
        )

        self.discovered_enemies = set()
        self.discovered_resources = set()
        self.discovered_zones = set()

        self.item_cooldowns = {}

        self.last_safe_zone_id = "starter_zone"

        self._add_debug_items()

    def update_last_safe_zone(self, zone_id):
        self.last_safe_zone_id = zone_id

    def get_target_info(self, zone, mouse_world, skill):
        item = self.active_item
        if not item:
            return None, None, None  # target, targeting_pos, radius

        # Step 1: compute direction from player to mouse
        direction = mouse_world - pygame.Vector2(self.rect.center)
        if direction.length_squared() > 0:
            direction = direction.normalize()
        targeting_pos = pygame.Vector2(self.rect.center) + direction * item.radius
        radius = item.radius

        # Step 2: gather targets
        if skill == "combat":
            targets = [e for e in zone.enemies if targeting_pos.distance_to(pygame.Vector2(e.rect.center)) <= radius]
        else:
            targets = [n for n in zone.resource_nodes if not n.depleted and n.skill == skill and targeting_pos.distance_to(pygame.Vector2(n.rect.center)) <= radius]

        # Step 3: find target under reticle or closest
        for target in targets:
            if target.rect.collidepoint((targeting_pos.x, targeting_pos.y)):
                return target, targeting_pos, radius

        if targets:
            closest = min(targets, key=lambda t: targeting_pos.distance_to(pygame.Vector2(t.rect.center)))
            return closest, targeting_pos, radius

        return None, targeting_pos, radius


    def change_active_item(self, index):
        self.inventory.selected_hotbar_index = index
        item_id = self.inventory.hotbar[index]

        self._unequip_active_item()

        if item_id:
            self._equip_active_item(item_id)
        else:
            self.active_item = self.fist

    def update(self, dt, zone_size):
        if self.freeze:
            return
        
        self.combat.set_active_effects(self.stats.active_effects)
        self.combat.update(dt)

        direction = self._get_movement_direction()

        if direction.length_squared() > 0:
            direction = direction.normalize()
            speed_bonus = self.stats.total_stats.get("speed", 0.0)
            multiplier = 1.0 + speed_bonus / 100
            multiplier = max(0.1, min(3.0, multiplier))
            self.pos += direction * self.base_speed * multiplier * dt

        self._clamp_position_to_zone(zone_size)

    def draw_attack_cooldown(self, surface, camera):
        item = self.active_item
        if not item or not hasattr(item, "get_cooldown_progress"):
            return

        progress = item.get_cooldown_progress(self)
        if progress >= 1.0:
            return

        w, h = 32, 6
        x = self.rect.centerx - w // 2
        y = self.rect.top - 10
        background_rect = pygame.Rect(x, y, w, h)
        progress_rect = pygame.Rect(x, y, w * progress, h)

        pygame.draw.rect(surface, (80, 80, 80), camera.apply(background_rect))
        pygame.draw.rect(surface, (200, 200, 50), camera.apply(progress_rect))

    def draw_targeting_overlay(self, screen, camera, target, targeting_pos, radius):
        if not self.active_item:
            return

        pos_screen = camera.apply(targeting_pos)
        pygame.draw.circle(screen, (100, 255, 100), pos_screen, radius, width=2)

        if target:
            highlight = target.rect.inflate(4, 4)
            pygame.draw.rect(screen, (255, 255, 0), camera.apply(highlight), width=2)

    def _equip_active_item(self, item_id):
        if self.active_item_id == item_id:
            return False

        item_data = self.inventory.get_item_full_data(item_id)
        base_data = item_data.base_data
        metadata = item_data.metadata or {}

        if not base_data:
            return False

        self.active_item = ActionItem(
            id=item_id,
            radius=base_data["radius"],
            delay=base_data["delay"],
            damage=base_data.get("weapon", {}).get("damage", 0),
            skill=base_data.get("skill", "combat"),
        )
        self.active_item_metadata = metadata
        self.active_item_id = item_id
        return True


    def _unequip_active_item(self):
        self.active_item = self.fist
        self.active_item_id = None
        self.active_item_metadata = {}

    def get_active_item_instance(self):
        return self.active_item

    def get_active_item_instance_metadata(self):
        return self.active_item_metadata

    def update_active_item_metadata(self, metadata):
        if not self.active_item_id or not self.inventory.is_item_instance(self.active_item_id):
            return
        instance_id = self.inventory._split_instance_id(self.active_item_id)[1]
        if instance_id in self.inventory.item_instances:
            self.inventory.item_instances[instance_id].metadata = metadata
            self.active_item_metadata = metadata

    def get_active_item_effect_sources(self):
        """Returns all ability IDs tied to the active weapon via enchantments or extra_ability field."""
        effect_ids = set()
        if not self.active_item_id:
            return effect_ids

        # 1. From enchantments stored in metadata as dicts
        metadata = self.get_active_item_instance_metadata()
        enchantments = metadata.get("enchantments", [])

        for enchant in enchantments:
            if isinstance(enchant, dict):
                enchant_id = enchant.get("id")
                enchant_data = ENCHANTMENT_DATA.get(enchant_id, {})
                ability_id = enchant_data.get("extra_ability")
                if ability_id in ABILITY_DATA:
                    effect_ids.add(ability_id)

        # 2. From weapon's own effect
        base_id = self.inventory.get_base_id(self.active_item_id)
        base_data = ITEMS.get(base_id, {})
        base_ability_id = base_data.get("extra_ability")
        if base_ability_id in ABILITY_DATA:
            effect_ids.add(base_ability_id)

        return effect_ids

    def _get_movement_direction(self):
        keys = pygame.key.get_pressed()
        direction = pygame.Vector2(0, 0)

        if keys[pygame.K_w]:
            direction.y -= self.base_speed
        if keys[pygame.K_s]:
            direction.y += self.base_speed
        if keys[pygame.K_a]:
            direction.x -= self.base_speed
        if keys[pygame.K_d]:
            direction.x += self.base_speed

        return direction

    def _clamp_position_to_zone(self, zone_size):
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))
        self.pos.x = max(0, min(self.pos.x, zone_size - self.rect.width))
        self.pos.y = max(0, min(self.pos.y, zone_size - self.rect.height))
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))

    def _add_debug_items(self):
        self.inventory.add_item("old_sword")
        self.inventory.add_item("stormblade", amount=1, metadata={
            "enchantments": [
                {"id": "chain_lightning", "level": 3},
            ]
        })
        self.inventory.add_item("grandmas_mittens")
        self.inventory.add_item("slime_crown")
        self.inventory.add_item("slime_chest")
        self.inventory.add_item("slime_gloves")
        self.inventory.add_item("slime_legs")
        self.inventory.add_item("slime_boots")
        self.inventory.add_item("phoenix_crown")
        self.inventory.add_item("phoenix_chest")
        self.inventory.add_item("phoenix_legs")
        self.inventory.add_item("phoenix_boots")
        self.inventory.add_item("iron_pickaxe")
        self.inventory.add_item("iron_axe")
        self.inventory.add_item("boots_of_speed")
        self.inventory.add_item("mantle_of_mending")

        self.inventory.add_item("slime_sword", amount=1)
        self.inventory.add_item("slime_sword", amount=1, metadata={
            "enchantments": [
                {"id": "sharpness", "level": 5},
                {"id": "first_hit_bonus", "level": 3},
                {"id": "cleave", "level": 3},
                {"id": "lifesteal", "level": 3},
                {"id": "speed_on_kill", "level": 3},
            ]
        })

        self.inventory.add_item("bone_plate", amount=1, metadata={
            "enchantments": [
                {"id": "steeled", "level": 5},
                {"id": "fortitude", "level": 5},
                {"id": "thorns", "level": 3},
            ]
        })
