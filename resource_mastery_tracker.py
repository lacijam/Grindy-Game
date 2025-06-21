from item_data import ITEMS
from format import *
from mastery_data import get_mastery_contribution_for_item

class ResourceMasteryTracker:
    def __init__(self, player):
        self.player = player
        self.resource_mastery_counts = {}
        self._resource_mastery_award_tracker = {
            "magic_find": 0
        }
        self.resource_mastery_bonuses = player.stats.resource_mastery_bonuses

    def apply_resource_mastery_gain(self, item_id, amount):
        item_data = ITEMS.get(item_id, {})

        # Direct mastery
        if item_data.get("category") == "resource" and "max_mastery_level" in item_data:
            self.resource_mastery_counts[item_id] = self.resource_mastery_counts.get(item_id, 0) + amount

        # Indirect mastery (via contribution table helper)
        contribution = get_mastery_contribution_for_item(item_id)
        for base_id, factor in contribution.items():
            self.resource_mastery_counts[base_id] = self.resource_mastery_counts.get(base_id, 0) + amount * factor

    def get_resource_mastery_count(self, resource_id):
        return self.resource_mastery_counts.get(resource_id, 0)

    def get_resource_mastery_total_entries(self):
        return len(self.resource_mastery_counts)

    def get_resource_mastery_level(self, resource_id):
        item = ITEMS.get(resource_id, None)
        if not item:
            return -1, []

        full_thresholds = [1, 50, 100, 250, 500, 1000, 2500, 5000, 10000, 25000, 50000, 100000]
        max_level = item.get("max_mastery_level", len(full_thresholds))
        thresholds = full_thresholds[:max_level]

        count = self.resource_mastery_counts.get(resource_id, 0)
        level = 0
        for t in thresholds:
            if count >= t:
                level += 1
            else:
                break
        return level, thresholds

    def get_total_resource_mastery_level(self):
        total = 0
        for resource_id in self.resource_mastery_counts:
            level, _ = self.get_resource_mastery_level(resource_id)
            total += level
        return total

    def get_max_total_resource_mastery_level(self):
        return sum(item.get("max_mastery_level", 0) for item in ITEMS.values())

    def get_resource_mastery_level_rewards(self, level):
        rewards = []
        for stat, bonus in self.resource_mastery_bonuses.items():
            if level % bonus["every"] == 0:
                rewards.append((stat, bonus["amount"]))
        return rewards
    
    def get_total_resource_bonuses(self):
        bonuses = []
        for stat, config in self.resource_mastery_bonuses.items():
            awarded = self._resource_mastery_award_tracker.get(stat, 0)
            bonus_total = awarded * config["amount"]
            bonuses.append((stat, bonus_total))
        return bonuses

    def check_total_mastery_rewards(self, message_log=None):
        total_level = self.get_total_resource_mastery_level()
        for stat, bonus in self.resource_mastery_bonuses.items():
            prev_awards = self._resource_mastery_award_tracker.get(stat, 0)
            new_awards = total_level // bonus["every"]
            if new_awards > prev_awards:
                gained = (new_awards - prev_awards) * bonus["amount"]
                self._resource_mastery_award_tracker[stat] = new_awards

                if message_log:
                    message_log.queue([
                        ("Mastery Milestone: ", get_colour_for_type("mastery")),
                        ("+", "white"),
                        (str(gained), get_colour_for_type("number")),
                        (f" {stat.replace('_', ' ').title()}", get_stat_colour(stat))
                    ])
