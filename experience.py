MAX_LEVEL = 60
_XP_THRESHOLDS = None

def round_to_nearest_magnitude(n):
    """Round number to the nearest 'nice' magnitude for XP display."""
    if n < 100:
        return round(n, -1)      # Nearest 10
    elif n < 1_000:
        return round(n, -2)      # Nearest 100
    elif n < 10_000:
        return round(n, -3)      # Nearest 1,000
    elif n < 100_000:
        return round(n, -4)      # Nearest 10,000
    else:
        return round(n, -5)      # Nearest 100,000

def generate_xp_table_from_deltas(
    levels=MAX_LEVEL,
    base_xp=1,
    starting_delta=150,
    initial_delta_growth_steps=1,
    initial_delta_multiplier=1.43,
    final_delta_multiplier=1.0,
):
    xp_table = []
    delta = starting_delta
    total_xp = 0
    step_counter = 0
    req = base_xp

    for level in range(0, levels + 1):
        if level == 1: # hardcode level to require 100xp
            delta_rounded = 99
            req += delta_rounded
        if level > 1:
            delta_rounded = round_to_nearest_magnitude(delta)
            req += delta_rounded

        total_xp += req
        xp_table.append((level, req, delta, total_xp))

        step_counter += 1

        dynamic_growth_steps = initial_delta_growth_steps + (level // 15)

        t = level / levels
        dynamic_multiplier = (1 - t) * initial_delta_multiplier + t * final_delta_multiplier

        if step_counter >= dynamic_growth_steps:
            delta = int(delta * dynamic_multiplier)
            step_counter = 0

    return xp_table


def get_xp_thresholds():
    global _XP_THRESHOLDS
    if _XP_THRESHOLDS is None:
        table = generate_xp_table_from_deltas()
        _XP_THRESHOLDS = [0] + [row[3] for row in table]  # prepend 0 for level 0
    return _XP_THRESHOLDS

def xp_required_for_level_up(level):
    thresholds = get_xp_thresholds()
    if level >= len(thresholds) - 1:
        return 0
    return thresholds[level + 1] - thresholds[level]

def total_xp_to_level(level):
    thresholds = get_xp_thresholds()
    return thresholds[level]  # already cumulative

def get_level(xp):
    thresholds = get_xp_thresholds()
    for level in range(1, MAX_LEVEL + 1):
        if xp < thresholds[level]:
            return level - 1
    return MAX_LEVEL

# Debug output
for lvl in range(0, MAX_LEVEL + 1):
    delta = xp_required_for_level_up(lvl) - xp_required_for_level_up(lvl - 1)
    print(f"Lv {lvl:2} → req {xp_required_for_level_up(lvl):,} - delta {delta:,} - total {total_xp_to_level(lvl):,}")