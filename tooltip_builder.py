import pygame

from format import *
from utils import *
from item_data import ITEMS
from set_bonus_data import SET_BONUS_DATA
from ability_data import ABILITY_DATA
from counter_data import COUNTER_DATA

# Tooltip Styling
TOOLTIP_BORDER_WIDTH = 1
TOOLTIP_WRAP_WIDTH = 200
TOOLTIP_PADDING = 10
TOOLTIP_LINE_SPACING = 5
TOOLTIP_BG_COLOUR = (50, 50, 50)
TOOLTIP_TEXT_COLOUR = (255, 255, 255)
TOOLTIP_DESCRIPTION_COLOUR = (200, 200, 200)
TOOLTIP_BORDER_COLOUR = (255, 255, 255)
TOOLTIP_WARNING_COLOUR = (180, 100, 100)
TOOLTIP_RECIPE_X_OFFSET = 500

PERCENTAGE_STATS = {"crit_chance", "crit_damage", "speed", "attack_speed"}

TOOLTIP_TEMPLATES = {
    "item": [
        {"field": "name", "style": "header"},
        {"field": "desc", "style": "wrap"},
        {"field": "weapon", "style": "base_damage"},
        {"field": "stat_bonuses", "style": "stat_lines"},
        {"field": "weapon", "style": "active_item_block"},
        {"field": "metadata", "style": "item_metadata"},
        {"field": "set", "style": "item_set_bonus"},
        {"field": "counter_id", "style": "counter_progress"},
        {"field": "rarity", "style": "rarity_label"},
    ],
    "enemy": [
        {"field": "enemy_label", "style": "enemy_label"},
        {"field": "hp", "style": "hp_line"},
        {"field": "drop_table", "style": "drop_table"},
    ],
    "resource_node": [
        {"field": "name", "style": "header"},
        {"field": "drop_table", "style": "drop_table"},
        {"field": "reward_xp", "style": "resource_xp"},
        {"field": "required_skills", "style": "resource_required_skills"},
    ],
    "portal": [
        {"field": "name", "style": "header"},
        {"field": "requirements", "style": "zone_requirements"},
    ],
    "beastiary_level": [
        {"field": "enemy_id", "style": "beastiary_info"},
    ],
    "total_beastiary": [
        {"field": "label", "style": "header"},
        {"field": "level", "style": "total_beastiary_line"},
    ],
    "skill": [
        {"field": "name", "style": "header"},
        {"field": "xp", "style": "skill_xp"},
        {"field": "bonus", "style": "skill_bonus"},
        {"field": "xp_rate", "style": "skill_xp_rate"},
        {"field": "eta_next", "style": "skill_eta"},
        {"field": "eta_60", "style": "skill_eta_60"},
    ],
    "stat": [
        {"field": "label", "style": "header"},
        {"field": "base", "style": "base_stat"},
        {"field": "sources", "style": "stat_sources"},
    ],
    "hp_healing_sources": [
        {"field": "name", "style": "header"},
        {"field": "healing_sources", "style": "hp_healing_sources"},
    ],
}

_queue = []

def queue_tooltip(tooltip_entry):
    _queue.append(tooltip_entry)

def get_tooltips():
    return list(_queue)

def clear_tooltips():
    _queue.clear()

def build_tooltip_lines_from_template(tooltip, ctx, template):
    lines = []
    data = tooltip["data"]

    if tooltip["type"] == "item":
        item_full_data = data
        
        merged_data = {}

        # Take the item object and merge all the fields into a dict for easier access
        merged_data = dict(item_full_data.base_data)
        merged_data["metadata"] = item_full_data.metadata
        merged_data["is_instance"] = item_full_data.is_instance
        merged_data["item_id"] = item_full_data.item_id

        data = merged_data

    for section in template:
        field = section["field"]
        style = section["style"]

        if not field in data:
            continue

        field_data = data.get(field, None)

        if style == "header":
            label = field_data
            lines.append((field_data, get_rarity_colour(label)))

        elif style == "wrap":
            lines.extend([(line, TOOLTIP_DESCRIPTION_COLOUR) for line in wrap_text(field_data, ctx.font, max_width=300)])

        elif style == "rarity_label":
            lines.append((" ", "white"))
            rarity = field_data
            lines.append((rarity.upper(), get_rarity_colour(rarity)))

        elif style == "enemy_label":
            enemy_level, enemy_name = field_data
            # TODO can we just pass this into the tooltip?
            player_level = ctx.player.skills.get_skill_level("combat")
            level_colour = get_enemy_level_colour(enemy_level, player_level)
            lines.append([(enemy_name, "white"), (" - Lv ", "white"), (str(enemy_level), level_colour)])

        elif style == "base_damage":
            weapon = data.get("weapon", {})
            damage = weapon.get("damage", None)
            if damage is not None:
                lines.append([
                    ("+", "white"),
                    (f"{int(damage)}", get_colour_for_type("number")),
                    (" Damage", "white")
                ])

        elif style == "stat_lines":
            for stat, val in field_data.items():
                label = get_stat_display_name(stat).title()
                stat_colour = get_stat_colour(stat)
                number_colour = get_colour_for_type("number")

                line = [("+" if val >= 0 else "-", "white"), (f"{abs(int(val))}", number_colour)]
                if stat in PERCENTAGE_STATS:
                    line.append(("%", "white"))

                line.append((f" {label}", stat_colour))
                lines.append(line)

        elif style == "item_metadata":
            metadata = field_data
            enchantments = metadata.get("enchantments", [])
            if not enchantments:
                continue
            
            lines.append((" ", "white"))

            lines.append([("Enchantments:", get_colour_for_type("highlight"))])
            for enchant in enchantments:
                ench_id = enchant["id"]
                ench_level = enchant["level"]
                ench_name = get_enchantment_display_name(ench_id)
                # TODO hardcoded colour
                lines.append([(f"    {ench_name} {ench_level}", (180, 180, 255))])

        elif style == "item_set_bonus":
            base_data = data
            set_id = base_data.get("set")
            if not set_id:
                continue

            set_data = SET_BONUS_DATA.get(set_id)
            if not set_data:
                continue

            lines.append((" ", "white")) # space

            set_display_name = set_data.get("name", set_id)
            bonuses_by_count = set_data.get("bonuses", {})

            # Count equipped pieces of this set
            equipped_count = 0
            for slot_entry in ctx.player.equipment.slots.values():
                if not slot_entry:
                    continue
                item_full_data = ctx.player.inventory.get_item_full_data(slot_entry.item_id)
                if item_full_data.base_data.get("set") == set_id:
                    equipped_count += 1

            lines.append([(f"{set_display_name}:", (100, 255, 100))])  # Header

            for tier in sorted(bonuses_by_count.keys()):
                bonuses = bonuses_by_count[tier]

                # Determine colour
                if equipped_count >= tier:
                    if equipped_count == tier:
                        colour = get_colour_for_type("set_bonus_current")
                    else:
                        colour = get_colour_for_type("set_bonus_unlocked")
                else:
                    colour = get_colour_for_type("set_bonus_locked")

                # Build tier header line with first bonus inline if possible
                first_line = [(f"({tier})", colour)]

                stat_lines = [
                    (stat, value)
                    for stat, value in bonuses.items()
                    if stat in ctx.player.stats.base_stats
                ]

                if stat_lines:
                    # Add first stat to same line
                    stat, value = stat_lines[0]
                    label = get_stat_display_name(stat).title()
                    stat_colour = get_stat_colour(stat)
                    number_colour = get_colour_for_type("number")

                    first_line.extend([
                        (" +", "white"),
                        (f"{int(value)}", number_colour)
                    ])
                    if stat in PERCENTAGE_STATS:
                        first_line.append(("%", "white"))

                    first_line.append((f" {label}", stat_colour))

                lines.append(first_line)

                # Any remaining stat bonuses → new lines
                for stat, value in stat_lines[1:]:
                    label = get_stat_display_name(stat).title()
                    stat_colour = get_stat_colour(stat)
                    number_colour = get_colour_for_type("number")

                    line = [
                        ("    +", "white"),
                        (f"{int(value)}", number_colour)
                    ]
                    if stat in PERCENTAGE_STATS:
                        line.append(("%", "white"))

                    line.append((f" {label}", stat_colour))
                    lines.append(line)
                
                extra_ability = bonuses.get("extra_ability")
                if extra_ability:
                    effect_data = ABILITY_DATA.get(extra_ability, {})
                    name = effect_data.get("name", extra_ability.title())
                    desc = effect_data.get("description")  # fallback if no description_fn
                    desc_fn = effect_data.get("description_fn")
                    values = effect_data.get("values", {})

                    if desc_fn:
                        desc = desc_fn(values)

                    lines.append([("    - ", "white"), (f"{name}: ", (180, 180, 255)), (desc, (200, 200, 200))])

        elif style == "counter_progress":
            counter_id = field_data
            counter_data = COUNTER_DATA.get(counter_id)

            if not counter_data:
                return lines
            
            lines.append((" ", "white"))
            
            counter_type = counter_data.get("type", "kills")
            current = data.get("metadata", {}).get("counters", {}).get(counter_type, 0)
            thresholds = counter_data.get("tiers", [])
            bonuses = counter_data.get("bonuses", [])

            current_tier = -1
            next_tier_index = None

            for i, threshold in enumerate(thresholds):
                if current >= threshold:
                    current_tier = i
                elif next_tier_index is None:
                    next_tier_index = i

            # Section header
            counter_label = counter_data.get("name", counter_type.replace("_", " ").title())
            lines.append([
                ("Item Bonus: ", get_colour_for_type("highlight")), 
                (counter_label, (200, 200, 100))
            ])

            # Label and description
            desc = counter_data.get("description")
            if desc:
                lines.append([(desc, (180, 180, 180))])

            # Current bonus
            if 0 <= current_tier < len(bonuses):
                bonus = bonuses[current_tier]
                for stat, value in bonus.items():
                    stat_label = stat.replace("_", " ").title()
                    lines.append([(f"Current Bonus: +{value} {stat_label}", get_stat_colour(stat))])

            # Next bonus
            if next_tier_index is not None and next_tier_index < len(bonuses):
                next_bonus = bonuses[next_tier_index]
                threshold = thresholds[next_tier_index]
                for stat, value in next_bonus.items():
                    stat_label = stat.replace("_", " ").title()
                    lines.append([
                        (f"Next Bonus: +{value} {stat_label} (", (180, 180, 255)),
                        (str(current), (100, 255, 100)),
                        (" / ", (255, 255, 255)),
                        (str(threshold), (255, 100, 100)),
                        (")", (180, 180, 255))
                    ])
        elif style == "active_item_block":
            lines.append((" ", "white"))
            
            skill_type = field_data.get("skill", "combat")
            colour = get_colour_for_type(skill_type)

            if skill_type == "combat":
                label = "Weapon Info"
            else:
                label = "Tool Info"
            lines.append((f"{label}:", colour))

            # Range
            lines.append([ # TODO hardcoded colour
                ("    - Range: ", (200, 200, 200)),
                (str(data.get("radius", "—")), get_colour_for_type("number"))
            ])

            # Delay as seconds
            delay_ms = data.get("delay") # TODO remove type check
            delay_str = f"{delay_ms / 1000:.1f}s" if isinstance(delay_ms, (int, float)) else "—"
            lines.append([ # TODO hardcoded colour
                ("    - Delay: ", (200, 200, 200)),
                (delay_str, get_colour_for_type("number"))
            ])
        elif style == "hp_line": # TODO hardcoded colour
            lines.append((f"HP: {field_data}", (200, 100, 100)))

        elif style == "drop_table":
            drops = field_data
            lines.extend(format_drop_table_lines(drops))

        elif style == "resource_xp": # TODO hardcoded colour
            lines.append((f"XP: {field_data}", (180, 180, 255)))

        elif style == "resource_required_skills":
            for skill, level in field_data.items():
                player_level = ctx.player.skills.get_skill_level(skill)
                if player_level < level: # TODO hardcoded colour
                    lines.append((f"{skill.title()} Lv {level} required", (255, 100, 100)))

        elif style == "zone_requirements":
            for skill, level in field_data.items():
                current = ctx.player.skills.get_skill_level(skill)
                colour = (255, 255, 255) if current >= level else (255, 100, 100) # TODO hardcoded colour
                lines.append((f"{skill.title()} Lv {level} required", colour))

        elif style == "beastiary_info":
            enemy_id = field_data
            enemy_data = ENEMY_DATA.get(enemy_id, {})
            kills = ctx.player.beastiary.get_enemy_kill_count(enemy_id)
            level, thresholds = ctx.player.beastiary.get_enemy_beastiary_level(enemy_id)

            name = enemy_data.get("name", enemy_id).title()
            description = enemy_data.get("description", "")

            lines.append([(name, get_colour_for_type("highlight")), (f" - Lv {level}", get_colour_for_type("number"))])
            if description:
                lines.append([(" ", "white")])
                lines.append([(description, "white")])
                lines.append([(" ", "white")])

            lines.append([("Kills: ", "white"), (str(kills), get_colour_for_type("number"))])
            lines.append([(" ", "white")])

            # Stat bonuses (e.g. strength/magic_find vs this enemy)
            bonus_stats = ctx.player.beastiary.get_stat_bonus_against_enemy(enemy_id)
            if bonus_stats:
                lines.append([("Bonuses:", get_colour_for_type("highlight"))])
                for stat, value in bonus_stats.items():
                    stat_label = stat.replace("_", " ").title()
                    lines.append([(f"+{value}", get_colour_for_type("number")), (" ", "white"), (stat_label, "white")])
                lines.append([(" ", "white")])

            # Progress bar
            if level < len(thresholds):
                next_threshold = thresholds[level]
                progress_ratio = min(1, kills / next_threshold)
                progress_pct = int(progress_ratio * 100)
                dash_count = 30
                filled = int(progress_ratio * dash_count)
                empty = dash_count - filled
                dash_line = [("-", (80, 200, 80))] * filled + [("-", (100, 100, 100))] * empty

                lines.append([("Progress to Level ", "white"), (str(level + 1), get_colour_for_type("number")), (f": {progress_pct}%", "white")])
                lines.append(dash_line)
                lines.append([(f"{kills}/{next_threshold} kills", "white")])
                lines.append([(" ", "white")])

            # Level reward preview
            next_level = level + 1
            rewards = ctx.player.beastiary.get_enemy_beastiary_level_rewards(next_level)
            if rewards:
                lines.append([(f"Level {next_level} Rewards", get_colour_for_type("highlight"))])
                for stat, amount in rewards:
                    stat_label = stat.replace("_", " ").title()
                    lines.append([(f"+{amount}", get_colour_for_type("number")), (" ", "white"), (stat_label, "white")])

        elif style == "total_beastiary_line":
            level = field_data
            next_level = level + 1

            lines.append([("Total Level: ", "white"), (str(level), get_colour_for_type("number"))])

            # Show current bonuses from tracker
            for stat, bonus_total in ctx.player.beastiary.get_total_non_enemy_bonuses():
                stat_label = stat.replace("_", " ").title()
                lines.append([
                    ("+", "white"),
                    (str(format_number_short(bonus_total)), get_colour_for_type("number")),
                    (" ", "white"),
                    (stat_label, get_stat_colour(stat))
                ])

            # Show next level rewards
            rewards = ctx.player.beastiary.get_beastiary_level_rewards(next_level)
            if rewards:
                lines.append([("Next Level Reward:", "white")])
                for stat, amount in rewards:
                    stat_label = stat.replace("_", " ").title()
                    lines.append([
                        (f"+{format_number_short(amount)}", get_colour_for_type("number")),
                        (" ", "white"),
                        (stat_label, get_stat_colour(stat))
                    ])
        elif style == "skill_xp":
            lines.append([
                ("XP: ", (200, 200, 200)),
                (f"{field_data}", get_colour_for_type("number"))
            ])

        elif style == "skill_bonus":
            label = field_data.get("label", "Bonus")
            text = field_data.get("text", "-")
            colour = field_data.get("colour", (255, 255, 255))
            lines.append([
                (f"{label}: ", colour),
                ("+", get_colour_for_type("white")),
                (text, get_colour_for_type("number")),
            ])
        elif style == "hp_healing_sources":
            # Vitality
            vitality = ctx.player.stats.total_stats.get("vitality", 0)
            if vitality > 0:
                lines.append([("Vitality", (180, 180, 255)), (f" +{int(vitality)}", (200, 200, 200))])

            sources = field_data
            for source in sources:
                lines.append([(f"{source}", get_colour_for_type("set_bonus_unlocked"))])

        elif style == "stat_sources":
            stat = getattr(ctx, "stat", None)
            sources = field_data

            if not sources:
                lines.append([("No Bonuses", (120, 120, 120))])
            else:
                if stat == "strength":
                    total = ctx.player.stats.total_stats.get("strength", 0)
                    lines.append([
                        ("Damage Increase: ", "white"),
                        (f"{total:.1f}", get_colour_for_type("number")),
                        ("%", "white")
                    ])
                elif stat == "speed":
                    total = ctx.player.stats.total_stats.get("speed", 0)
                    lines.append([
                        ("Movement Speed Increase: ", "white"),
                        (f"{total:.1f}", get_colour_for_type("number")),
                        ("%", "white")
                    ])
                elif stat == "attack_speed":
                    total = ctx.player.stats.total_stats.get("attack_speed", 0)
                    lines.append([
                        ("Attack Delay Reduction: ", "white"),
                        (f"{total:.1f}", get_colour_for_type("number")),
                        ("%", "white")
                    ])
                elif stat == "defense":
                    reduction_percent = ctx.player.stats.calculate_damage_reduction() * 100
                    lines.append([
                        ("Damage Reduction: ", "white"), 
                        (f"{reduction_percent:.1f}", get_colour_for_type("number")),
                        ("%", "white")]
                    )
                elif stat == "vitality":
                    total = ctx.player.stats.total_stats.get("vitality", 0)
                    lines.append([
                        ("Health Gain: ", "white"), 
                        (f"{total}", get_colour_for_type("number")),
                        (" / second", "white")]
                    )

                grouped_data = {
                    "character": [],
                    "active": [],
                    "active-enchant": [],
                    "gear": [],
                    "gear-enchant": [],
                }

                # sort into groups
                for entry in field_data:
                    grouped_data.get(entry.source_category, grouped_data["gear"]).append(
                        (entry.source_name, entry.amount)
                    )

                # render in order
                for group in grouped_data.keys():
                    group_entries = grouped_data[group]
                    if not group_entries:
                        continue

                    # add section header
                    group_label = {
                        "character": "From Character:",
                        "active": "From Active Item:",
                        "active_enchant": "From Active Item Enchantments:",
                        "gear": "From Equipped Gear:",
                        "gear-enchant": "From Gear Enchantments:",
                    }.get(group, f"From {group.title()}:")

                    # divider line
                    lines.append([("-" * 30, (80, 80, 80))])
                    lines.append([(group_label, "white")])

                    # sort descending by value
                    sorted_group = sorted(grouped_data[group], key=lambda x: abs(x[1]), reverse=True)
                    for label, value in sorted_group:
                        desc = describe_stat_bonus(stat, value)
                        lines.append([
                            (f"    {label}: ", "white"),
                            ("+", (255, 255, 255)),
                            (desc["formatted"], get_colour_for_type("number"))
                        ])
        elif style == "base_stat":
            base = field_data
            if base > 0:
                lines.append([
                    ("Base: ", (180, 180, 180)),
                    (str(base), get_colour_for_type("number"))
                ])
        elif style == "skill_eta":
            lines.append([
                ("Time to Next Lv: ", (200, 200, 200)),
                (field_data, (180, 220, 255))
            ])
        elif style == "skill_eta_60":
            lines.append([
                ("Time to Level 60: ", (200, 200, 200)),
                (field_data, (180, 220, 255))
            ])
        elif style == "skill_xp_rate":
            lines.append([
                ("XP/hour: ", (200, 200, 200)),
                (f"{field_data}", (255, 255, 150))
            ])

    return lines

def build_tooltip_lines(tooltip, ctx):
    if tooltip["type"] == "custom":
        return tooltip["data"]

    template = TOOLTIP_TEMPLATES.get(tooltip["type"])
    if not template:
        return []

    return build_tooltip_lines_from_template(tooltip, ctx, template)

def draw_tooltip_lines(screen, lines, font, pos):
    rendered_lines = []
    max_width = 0
    line_height = font.get_height()

    for line in lines:
        if isinstance(line, list):
            parts = [(font.render(text, True, colour), colour) for text, colour in line]
            line_width = sum(part.get_width() for part, _ in parts)
            rendered_lines.append(parts)
        else:
            text, colour = line
            part = font.render(text, True, colour)
            rendered_lines.append([(part, colour)])
            line_width = part.get_width()

        max_width = max(max_width, line_width)

    width = max_width + TOOLTIP_PADDING * 2
    height = len(rendered_lines) * (line_height + TOOLTIP_LINE_SPACING) + TOOLTIP_PADDING

    x, y = clamp_to_screen(pos[0], pos[1], width, height)

    pygame.draw.rect(screen, TOOLTIP_BG_COLOUR, (x, y, width, height))
    pygame.draw.rect(screen, TOOLTIP_BORDER_COLOUR, (x, y, width, height), TOOLTIP_BORDER_WIDTH)

    y_offset = y + TOOLTIP_PADDING
    for line_parts in rendered_lines:
        x_offset = x + TOOLTIP_PADDING
        for surf, _ in line_parts:
            screen.blit(surf, (x_offset, y_offset))
            x_offset += surf.get_width()
        y_offset += line_height + TOOLTIP_LINE_SPACING
