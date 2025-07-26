import pygame
from format import *
from experience import *
from dataclasses import dataclass

ONE_HOUR_MS = 3600000
XP_LOG_RETENTION_MS = 2 * ONE_HOUR_MS

@dataclass(frozen=True)
class LogEntry:
    timestamp: int
    cumulative_xp: int

class PlayerSkills:
    def __init__(self, player):
        self.player = player
        self.skill_xp = {
            "combat": 0,
            "mining": 0,
            "woodcutting": 0
        }
        self.xp_time_log = {skill: [] for skill in self.skill_xp}

    def gain_xp(self, skill, amount):
        now = pygame.time.get_ticks()
        self.skill_xp[skill] = self.skill_xp.get(skill, 0) + amount

        log = self.xp_time_log[skill]
        last_cum_xp = self._latest_cumulative_xp(log)
        new_cum_xp = last_cum_xp + amount
        log.append(LogEntry(timestamp=now, cumulative_xp=new_cum_xp))

        self._prune_old_xp_entries(skill, XP_LOG_RETENTION_MS)

    def xp_per_hour(self, skill):
        now = pygame.time.get_ticks()
        cutoff = now - ONE_HOUR_MS

        log = self.xp_time_log.get(skill, [])
        if not log:
            return 0

        start_xp, start_ts = self._starting_xp_in_window(log, cutoff)
        current_xp = self._latest_cumulative_xp(log)
        current_ts = self._latest_timestamp(log)

        xp_gained = current_xp - start_xp
        elapsed_ms = max(current_ts - start_ts, 1)
        hours = elapsed_ms / ONE_HOUR_MS

        return xp_gained / hours

    def time_until_level_up(self, skill, target_level=None):
        xp = self.skill_xp.get(skill, 0)
        current_level = self.get_skill_level(skill)

        if target_level is None:
            target_level = current_level + 1

        xp_needed = total_xp_to_level(target_level)
        remaining_xp = xp_needed - xp

        current_rate = max(self.xp_per_hour(skill), 1e-6)
        if current_rate <= 0 or remaining_xp <= 0:
            return None

        return remaining_xp / current_rate

    def get_skill_level(self, skill):
        xp = self.skill_xp.get(skill, 0)
        return get_level(xp)

    def get_level_progress(self, skill):
        xp = self.skill_xp.get(skill, 0)
        level = self.get_skill_level(skill)
        xp_needed = xp_required_for_level_up(level + 1)
        xp_into_level = xp - total_xp_to_level(level)

        return xp_into_level / xp_needed if xp_needed > 0 else 1.0

    def get_skill_progress(self):
        progress_list = []

        for skill, xp in self.skill_xp.items():
            level = get_level(xp)
            xp_into_level = xp - total_xp_to_level(level)
            xp_needed = total_xp_to_level(level + 1) - total_xp_to_level(level)
            progress_list.append((skill, level, xp_into_level, xp_needed))

        return progress_list

    def get_skill_total_xp(self, skill):
        return self.skill_xp.get(skill, 0)

    def _prune_old_xp_entries(self, skill, retention_ms):
        now = pygame.time.get_ticks()
        cutoff = now - retention_ms

        self.xp_time_log[skill] = [
            entry for entry in self.xp_time_log[skill]
            if entry.timestamp >= cutoff
        ]

    def _starting_xp_in_window(self, log, cutoff):
        start_xp = None
        start_ts = None

        for entry in reversed(log):
            if entry.timestamp < cutoff:
                break
            start_xp = entry.cumulative_xp
            start_ts = entry.timestamp

        if start_xp is None:
            start_xp = log[0].cumulative_xp
            start_ts = log[0].timestamp

        return start_xp, start_ts
    
    def _latest_cumulative_xp(self, log):
        if not log:
            return 0
        return log[-1].cumulative_xp

    def _latest_timestamp(self, log):
        if not log:
            return 0
        return log[-1].timestamp