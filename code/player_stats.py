import pygame

from dataclasses import dataclass
from data.set_bonus_data import SET_BONUS_DATA
from data.enchantment_data import ENCHANTMENT_DATA
from data.ability_data import ABILITY_DATA
from data.counter_data import COUNTER_DATA

@dataclass(frozen=True)
class StatSourceEntry:
    source_category: str
    source_name: str
    amount: float

class PlayerStats:
    def __init__(self, player):
        self.player = player

        self.base_stats = {
            "strength": 0,
            "max_hp": 100,
            "defense": 0,
            "speed": 0,
            "crit_chance": 25,
            "crit_damage": 50,
            "attack_speed": 0,
            "vitality": 1,
            "magic_find": 0,
            "tool_speed": 0
        }

        self.stat_sources = {stat: [] for stat in self.base_stats}
        self.active_effects = []
        self.active_set_bonuses = {}
        self.temp_stat_bonuses = {}

        self.level_up_bonuses = {
            "combat": {"stat": "crit_chance", "per_level": 0.5},
            "mining": {"stat": "defense", "per_level": 5},
            "woodcutting": {"stat": "strength", "per_level": 1},
        }

        self.beastiary_bonuses = {
            "max_hp": {"amount": 1, "every": 1},
            "combat_xp": {"amount": 1000, "every": 5},
            "enemy": {"strength": 1, "magic_find": 1},
        }

    def _rebuild_stat_sources(self):
        self.active_effects.clear()

        self.stat_sources = {stat: [] for stat in self.base_stats}

        self._add_level_up_bonuses()
        self._add_active_item_bonuses()
        self._add_equipment_bonuses()
        self._add_equipment_set_bonuses()
        self._add_beastiary_bonuses()
        self._add_temp_stat_bonuses()

    def is_item_in_active_set(self, item_id):
        for bonus in self.active_set_bonuses.values():
            if item_id in bonus["contributors"]:
                return True
        return False

    def get_active_set_bonus_effect_ids(self):
        effect_ids = []
        for bonus in self.active_set_bonuses.values():
            effect_ids.extend(bonus.get("effect_ids", []))
        return effect_ids

    def _add_equipment_set_bonuses(self):
        self.active_set_bonuses.clear()
        set_counts = {}

        # Count equipped items per set
        for slot_entry in self.player.equipment.slots.values():
            if not slot_entry:
                continue

            item_full_data = self.player.inventory.get_item_full_data(slot_entry.item_id)
            base_data = item_full_data.base_data

            set_name = base_data.get("set")
            if not set_name:
                continue

            set_counts.setdefault(set_name, {"count": 0, "contributors": []})
            set_counts[set_name]["count"] += 1
            set_counts[set_name]["contributors"].append(slot_entry.item_id)

        # Apply bonuses and record effect data
        for set_name, info in set_counts.items():
            count = info["count"]
            contributors = info["contributors"]
            set_data = SET_BONUS_DATA.get(set_name, {})
            set_display_name = set_data.get("name", set_name)
            bonuses_by_count = set_data.get("bonuses", {})

            active_effect_ids = []

            for pieces_required, bonuses in bonuses_by_count.items():
                if count >= pieces_required:
                    for stat, bonus in bonuses.items():
                        if stat in {"custom", "extra_ability"}:
                            continue  # custom logic handled separately
                        entry = StatSourceEntry("set", f"{set_display_name} ({pieces_required} pcs)", bonus)
                        self.stat_sources[stat].append(entry)

                    extra_ability = bonuses.get("extra_ability")
                    if extra_ability:
                        active_effect_ids.append(extra_ability)
                        self.active_effects.append({
                            "id": extra_ability,
                            "tier": pieces_required,
                            "set_name": set_display_name,
                        })

            # Cache active set bonus info
            self.active_set_bonuses[set_name] = {
                "count": count,
                "contributors": contributors,
                "effect_ids": active_effect_ids,
            }

    def _add_temp_stat_bonuses(self):
        now = pygame.time.get_ticks()
        for stat, bonuses in self.temp_stat_bonuses.items():
            for amount, expiry in bonuses:
                if expiry > now:
                    entry = StatSourceEntry("temp", "Temporary Bonus", amount)
                    self.stat_sources[stat].append(entry)

    def _add_level_up_bonuses(self):
        for skill, bonus in self.level_up_bonuses.items():
            level = self.player.skills.get_skill_level(skill)
            stat = bonus["stat"]
            per_level = bonus["per_level"]
            amount = level * per_level

            entry = StatSourceEntry("character", f"{skill.capitalize()} Level", amount)
            self.stat_sources[stat].append(entry)

    def _add_active_item_bonuses(self):
        if not self.player.active_item_id:
            return

        item_full_data = self.player.inventory.get_item_full_data(self.player.active_item_id)
        base_data = item_full_data.base_data

        if not base_data:
            return

        for stat, bonus in base_data.get("stat_bonuses", {}).items():
            name = base_data.get("name", "Unnamed Active")
            entry = StatSourceEntry("active", name, bonus)
            self.stat_sources[stat].append(entry)

        enchant_bonuses = self.player.inventory.get_enchantment_stat_bonuses_for_item(self.player.active_item_id)
        for stat, bonus in enchant_bonuses.items():
            entry = StatSourceEntry("active-enchant", "Active Enchantments", bonus)
            self.stat_sources[stat].append(entry)

        enchantments = self.player.inventory.get_enchantments_for_item(self.player.active_item_id)
        for enchant in enchantments:
            enchant_id = enchant["id"]
            enchant_level = enchant["level"]

            self.active_effects.append({
                "id": enchant_id,
                "tier": enchant_level,
                "set_name": base_data.get("name", "Unnamed Active"),
            })

        counter_id = base_data.get("counter_id")
        counter_data = COUNTER_DATA.get(counter_id)
        if counter_data:
            counter_type = counter_data.get("type")
            counter_value = item_full_data.metadata.get("counters", {}).get(counter_type, 0)
            tier_thresholds = counter_data.get("tiers", [])
            bonuses = counter_data.get("bonuses", [])

            current_tier = 0
            for i, threshold in enumerate(tier_thresholds):
                if counter_value >= threshold:
                    current_tier = i
                else:
                    break

            if tier_thresholds and counter_value >= tier_thresholds[0] and current_tier < len(bonuses):
                tier_bonus = bonuses[current_tier]
                base_name = counter_data.get("name", "Counter")
                name_with_tier = f"{base_name} (Tier {current_tier + 1})"
                for stat, value in tier_bonus.items():
                    entry = StatSourceEntry("counter", name_with_tier, value)
                    self.stat_sources[stat].append(entry)


    def _add_equipment_bonuses(self):
        for slot, slot_entry in self.player.equipment.slots.items():
            if not slot_entry:
                continue

            item_id = slot_entry.item_id
            metadata = slot_entry.metadata

            item_full_data = self.player.inventory.get_item_full_data(item_id)
            base_data = item_full_data.base_data

            if not base_data:
                return
            
            for stat, bonus in base_data.get("stat_bonuses", {}).items():
                name = base_data.get("name", "Unnamed Gear")
                entry = StatSourceEntry("gear", name, bonus)
                self.stat_sources[stat].append(entry)

            enchantments = self.player.inventory.get_enchantments_for_item(item_id, metadata_override=metadata)
            for enchant in enchantments:
                enchant_id = enchant["id"]
                enchant_level = enchant["level"]

                # Stat bonuses if any
                item_data = ENCHANTMENT_DATA.get(enchant_id, {})
                stat_bonuses = item_data.get("stat_bonuses_per_level", {})

                for stat, per_level_bonus in stat_bonuses.items():
                    amount = per_level_bonus * enchant_level
                    gear_name = base_data.get("name", "Unnamed Gear")
                    entry = StatSourceEntry("gear-enchant", f"{gear_name} Enchantments", amount)
                    self.stat_sources[stat].append(entry)

                # Add to active_effects
                self.active_effects.append({
                    "id": enchant_id,
                    "tier": enchant_level,
                    "set_name": base_data.get("name", "Unnamed Gear"),
                })

    def get_total_stats_with_enemy_bonus(self, target):
        bonus_enemy_stats = self.player.beastiary.get_stat_bonus_against_enemy(target.id)
        total_stats = dict(self.total_stats)

        for stat, value in bonus_enemy_stats.items():
            total_stats[stat] = total_stats.get(stat, 0) + value

        return total_stats

    def _add_beastiary_bonuses(self):
        beast_level = self.player.beastiary.get_total_beastiary_level()
        if beast_level <= 0:
            return

        entry = StatSourceEntry("character", "Beastiary Levels", beast_level)
        self.stat_sources["max_hp"].append(entry)

    def calculate_damage_reduction(self):
        defense = self.total_stats.get("defense", 0)
        if defense <= 0:
            return 0.0
        reduction = defense / (defense + 250)
        return min(reduction, 0.99)

    def add_temp_stat_bonus(self, stat, amount, duration):
        now = pygame.time.get_ticks()
        expiry_time = now + int(duration * 1000)

        if stat not in self.temp_stat_bonuses:
            self.temp_stat_bonuses[stat] = []

        self.temp_stat_bonuses[stat].append((amount, expiry_time))

    def _prune_temp_stat_bonuses(self):
        now = pygame.time.get_ticks()
        for stat in self.temp_stat_bonuses:
            self.temp_stat_bonuses[stat] = [
                (amount, expiry) for (amount, expiry) in self.temp_stat_bonuses[stat]
                if expiry > now
            ]

    def get_healing_sources(self):
        #TODO Get these dynamically from the data.
        HEALING_EFFECT_IDS = {"slime_regen"}

        sources = []
        for effect in self.active_effects:
            if effect["id"] in HEALING_EFFECT_IDS:
                effect_data = ABILITY_DATA.get(effect["id"])
                if not effect_data:
                    effect_data = ENCHANTMENT_DATA.get(effect["id"], {})

                name = effect_data.get("name", effect["id"].title())
                sources.append(name)

        return sources

    @property
    def total_stats(self):
        self._prune_temp_stat_bonuses()
        self._rebuild_stat_sources()
        return {
            k: self.base_stats[k]
            + sum(entry.amount for entry in self.stat_sources.get(k, []))
            + sum(amount for amount, expiry in self.temp_stat_bonuses.get(k, []) if expiry > pygame.time.get_ticks())
            for k in self.base_stats
        }
