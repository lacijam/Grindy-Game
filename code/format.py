from data.item_data import ITEMS

_COLOURS = {
    "common": (255, 255, 255),
    "uncommon": (50, 200, 50),
    "rare": (50, 100, 255),
    "epic": (180, 0, 255),
    "legendary": (255, 140, 0),
    "mythic": (255, 0, 0),
}

_STAT_DISPLAY_NAMES = {
    "strength": "Strength",
    "max_hp": "Health",
    "defense": "Defense",
    "speed": "Speed",
    "crit_chance": "Crit Chance",
    "crit_damage": "Crit Damage",
    "attack_speed": "Attack Speed",
    "vitality": "Vitality",
    "magic_find": "Magic Find",
    "tool_speed": "Tool Speed",
}

_STAT_COLOURS = {
    "strength": (255, 110, 110),
    "max_hp": (255, 180, 180),
    "defense": (100, 100, 255),
    "speed": (255, 255, 255),
    "crit_chance": (255, 255, 100),
    "crit_damage": (255, 200, 120),
    "attack_speed": (180, 255, 180),
    "vitality": (255, 90, 90),
    "magic_find": (255, 120, 255),
    "tool_speed": (160, 160, 160),
}

_STAT_FORMATS = {
    "strength": lambda x: f"{x}",
    "defense": lambda x: f"{x}",
    "max_hp": lambda x: f"{x}",
    "crit_chance": lambda x: f"{x:.1f}%",
    "crit_damage": lambda x: f"{x:.1f}%",
    "attack_speed": lambda x: f"{x:.1f}",
    "speed": lambda x: f"{x}%",
    "vitality": lambda x: f"{x}",
    "magic_find": lambda x: f"{x}%",
}

_SKILL_COLOURS = {
    "combat": (255, 80, 80),
    "mining": (80, 80, 255),
    "woodcutting": (80, 255, 80),
}

def get_enchantment_display_name(enchant_id):
    display_names = {
        "sharpness": "Sharpness",
        "crit_chance": "Crit Chance",
        "crit_damage": "Crit Damage",
        "attack_speed": "Attack Speed",
        "defense": "Defense",
        "hp": "HP",
        "magic_find": "Magic Find",
    }
    return display_names.get(enchant_id, enchant_id.replace("_", " ").title())

def get_colour_for_type(thing_type):
    return {
        "boss": (255, 100, 0),
        "zone": (180, 255, 180),
        "enemy": (255, 140, 125),
        "resource": (200, 255, 200),
        "mastery": (120, 255, 120),
        "beastiary": (255, 100, 120),
        "number": (150, 150, 255),
        "highlight": (200, 200, 200),
        "kill": (255, 80, 80),
        "mine": (80, 80, 255),
        "craft": (255, 165, 0),
        "reach_level": (80, 255, 80),
        "set_bonus_current": (100, 255, 100),
        "set_bonus_unlocked": (100, 255, 100),
        "set_bonus_locked": (100, 100, 100),
    }.get(thing_type, (255, 255, 255))

def get_contrasting_text_colour(bg_colour):
    r, g, b = bg_colour
    brightness = (r * 299 + g * 587 + b * 114) / 1000
    return (0, 0, 0) if brightness > 150 else (255, 255, 255)

def get_rarity_colour(rarity):
    return _COLOURS.get(rarity, (255, 255, 255))

def get_rarity_colours():
    return _COLOURS.keys()

def get_stat_colour(stat):
    return _STAT_COLOURS.get(stat, (255, 255, 255))

def get_stat_display_name(stat):
    return _STAT_DISPLAY_NAMES.get(stat, "Unknown").title()

def get_stat_format(stat):
    return _STAT_FORMATS.get(stat, lambda x: f"{x}")

def get_skill_colour(skill):
    return _SKILL_COLOURS.get(skill, (255, 255, 255))

def get_enemy_level_colour(enemy_level, player_level):
    diff = enemy_level - player_level

    if diff >= 5:
        return (180, 80, 255)  # Purple
    elif diff >= 3:
        return (255, 80, 80)   # Red
    elif -1 <= diff <= 1:
        return (80, 255, 80)   # Green
    elif diff < -1:
        return (80, 160, 255)  # Blue

    return (200, 200, 200)     # Default grey fallback

# used for tooltip and message
def describe_stat_bonus(stat, amount):
    label = get_stat_display_name(stat)
    colour = get_stat_colour(stat)
    fmt = get_stat_format(stat)
    formatted = fmt(amount)
    return {
        "label": label,
        "colour": colour,
        "formatted": formatted,
    }

def get_drop_chance_display(item_id, source):
    # `source` could be an enemy or resource node
    drop_table = getattr(source, "drop_table", [])
    for drop in drop_table:
        if drop[0] == item_id:
            chance = drop[1]
            return f"{round(chance * 100)}%" if chance < 1 else f"{int(chance * 100)}%"
    return "??%"


def format_number_short(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}m"
    elif n >= 10_000:
        return f"{n // 1000}k"
    elif n >= 1_000:
        return f"{n / 1000:.1f}k"
    return str(n)

def format_time_hours(hours):
    if hours is None:
        return "?"
    total_seconds = int(hours * 3600)
    h = total_seconds // 3600
    m = (total_seconds % 3600) // 60
    s = total_seconds % 60
    
    if h > 0 and m > 0:
        return f"{h}h {m}m"
    elif h > 0:
        return f"{h}h"
    elif m > 0:
        return f"{m}m"
    else:
        return f"{s}s"

def format_drop_table_lines(tiered_drop_table, label="Drops:"):
    lines = []
    if not tiered_drop_table:
        return lines

    lines.append((label, (200, 200, 200)))

    rarity_order = list(get_rarity_colours())

    def tier_sort_key(tier):
        return rarity_order.index(tier) if tier in rarity_order else len(rarity_order)

    def item_rarity_key(drop):
        item_id = drop[0]
        item_data = ITEMS.get(item_id, {})
        rarity = item_data.get("rarity", "common")
        return rarity_order.index(rarity) if rarity in rarity_order else len(rarity_order)

    # common to mythic
    sorted_tiers = sorted(tiered_drop_table.items(), key=lambda x: tier_sort_key(x[0]))

    for tier, drops in sorted_tiers:
        if not drops:
            continue

        lines.append((f"{tier.title()} Loot", get_rarity_colour(tier)))

        # Sort entries in this tier by item rarity (most common first)
        sorted_drops = sorted(drops, key=item_rarity_key)

        for drop in sorted_drops:
            item_id = drop[0]
            chance = drop[1] if len(drop) > 1 else 1.0
            quantity = drop[2] if len(drop) > 2 else (1, 1)

            item_data = ITEMS.get(item_id, {})
            name = item_data.get("name", item_id).title()
            colour = get_rarity_colour(item_data.get("rarity", "common"))

            min_qty, max_qty = quantity
            if min_qty == max_qty == 1:
                qty_str = ""
            elif min_qty == max_qty:
                qty_str = f" x{min_qty}"
            else:
                qty_str = f" x{min_qty}-{max_qty}"

            chance_str = f"{round(chance * 100, 5)}%"

            lines.append((f"    - {name}{qty_str} — {chance_str}", colour))

    return lines
