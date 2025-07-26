from data.enemy_data import ENEMY_DATA
from format import *

class BeastiaryTracker:
    def __init__(self, player):
        self.player = player
        self.enemy_kill_counts = {}
        self._beastiary_award_tracker = {
            "max_hp": 0,
            "combat_xp": 0
        }
        self.beastiary_bonuses = player.stats.beastiary_bonuses

    def get_enemy_beastiary_level(self, enemy_id):
        kills = self.enemy_kill_counts.get(enemy_id, 0)
        thresholds = self._get_enemy_thresholds(enemy_id)
        level = 0
        for threshold in thresholds:
            if kills >= threshold:
                level += 1
            else:
                break
        return level, thresholds

    def get_total_beastiary_level(self):
        total = 0
        for enemy_id, kills in self.enemy_kill_counts.items():
            thresholds = self._get_enemy_thresholds(enemy_id)
            for threshold in thresholds:
                if kills >= threshold:
                    total += 1
                else:
                    break
        return total

    def get_max_total_beastiary_level(self):
        return sum(enemy.get("beastiary", {}).get("max_level", 0) for enemy in ENEMY_DATA.values())

    def get_beastiary_level_rewards(self, level):
        rewards = []
        for stat, config in self.beastiary_bonuses.items():
            if stat == "enemy":
                continue
            if level % config["every"] == 0:
                rewards.append((stat, config["amount"]))
        return rewards

    def get_enemy_beastiary_level_rewards(self, level):
        rewards = []
        enemy_bonus_config = self._get_enemy_bonus_config()
        for stat, per_level_bonus in enemy_bonus_config.items():
            rewards.append((stat, per_level_bonus * level))
        return rewards

    def get_total_non_enemy_bonuses(self):
        bonuses = []
        for stat, config in self.beastiary_bonuses.items():
            if stat == "enemy":
                continue
            awarded = self._beastiary_award_tracker.get(stat, 0)
            bonus_total = awarded * config["amount"]
            bonuses.append((stat, bonus_total))
        return bonuses

    def get_stat_bonus_against_enemy(self, enemy_id):
        level, _ = self.get_enemy_beastiary_level(enemy_id)
        bonus_config = self._get_enemy_bonus_config()
        return {
            stat: level * value
            for stat, value in bonus_config.items()
        }

    def get_enemy_kill_count(self, enemy_id):
        return self.enemy_kill_counts.get(enemy_id, 0)

    def update_enemy_kill_count(self, enemy_id, new_value):
        self.enemy_kill_counts[enemy_id] = new_value

    def check_total_beastiary_rewards(self, handle_gainxp_fn=None, message_log_callback=None):
        total_level = self.get_total_beastiary_level()
        for stat, bonus in self.beastiary_bonuses.items():
            if stat == "enemy":
                continue

            prev_awards = self._beastiary_award_tracker.get(stat, 0)
            new_awards = total_level // bonus["every"]

            if new_awards > prev_awards:
                gained = (new_awards - prev_awards) * bonus["amount"]
                self._beastiary_award_tracker[stat] = new_awards

                self._apply_beastiary_reward(stat, gained, handle_gainxp_fn, message_log_callback)

    def _get_enemy_thresholds(self, enemy_id):
        return ENEMY_DATA.get(enemy_id, {}).get("beastiary", {}).get("thresholds", [])

    def _get_enemy_bonus_config(self):
        return self.beastiary_bonuses.get("enemy", {})

    def _apply_beastiary_reward(self, stat, gained, handle_gainxp_fn, message_log_callback):
        if stat == "combat_xp" and handle_gainxp_fn:
            handle_gainxp_fn("combat", gained)

        if message_log_callback:
            message_log_callback.queue([
                ("Beastiary Milestone: ", get_colour_for_type("beastiary")),
                ("+", "white"),
                (str(gained), get_colour_for_type("number")),
                (" ", "white"),
                (stat.replace("_", " ").title(), get_stat_colour(stat))
            ])