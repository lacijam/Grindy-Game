import pygame

import math

from constants import *
from enemy_data import ENEMY_DATA

class UseResult:
    def __init__(self, target=None, final_damage=None):
        self.partial_xp = {}       # e.g. {"mining": 2}
        self.partial_drops = {}    # e.g. {"stone": 1}

        self.final_hit = False
        self.final_xp = {}         # e.g. {"mining": 20}
        self.final_drops = {}      # e.g. {"iron_ore": 1}

        self.target = target # Reference to the target for further handling

    def has_any(self):
        return (
            self.partial_xp or self.partial_drops or
            self.final_xp or self.final_drops or self.final_hit
        )

def to_panel_space(global_pos, panel_rect):
    return (global_pos[0] - panel_rect.x, global_pos[1] - panel_rect.y)

def get_beastiary_progress(enemy_id, kill_count):
    data = ENEMY_DATA.get(enemy_id, {})
    bdata = data.get("beastiary", {})
    thresholds = bdata.get("thresholds", [])

    level = 0
    for required in thresholds:
        if kill_count >= required:
            level += 1
        else:
            break

    # Progress to next level (0–1 float)
    if level < len(thresholds):
        prev = thresholds[level - 1] if level > 0 else 0
        next_req = thresholds[level]
        progress = (kill_count - prev) / (next_req - prev)
    else:
        progress = 1.0  # maxed

    return level, progress

def calculate_shake_intensity(damage, is_crit=False):
    base = damage * 0.15
    if is_crit:
        base *= 1.5
    return min(base, 6)

def recipe_is_unlocked(recipe, player):
    requirements = recipe.get("requirements", {})
    for skill, required_level in requirements.items():
        if player.skills.get_skill_level(skill) < required_level:
            return False
    return True

def clamp_to_screen(x, y, width, height):
    screen = pygame.display.get_surface()
    screen_width = screen.get_width()
    screen_height = screen.get_height()

    x = min(x, screen_width - width - 5)
    x = max(x, 5)

    y = min(y, screen_height - height - 5)
    y = max(y, 5)

    return x, y

def wrap_text(text, font, max_width):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines