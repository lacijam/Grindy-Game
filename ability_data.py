ABILITY_DATA = {
    "slime_shield": {
        "name": "Slime Shield",
        "values": {
            "damage_reduction_percent": 50,
        },
        "description_fn": lambda values: handle_slime_shield_description(values),
    },
    "slime_regen": {
        "name": "Slime Regeneration",
        "values": {
            "interval": 2000,
            "regen_percent": 0.02,
        },
        "description_fn": lambda values: handle_slime_regen_description(values),
    },
    "bone_thorns": {
        "name": "Bone Thorns",
        "values": {
            "reflect_percent": 0.05,
        },
        "description_fn": lambda values: handle_bone_thorns_description(values),
    },
    "phoenix_aura": {
        "name": "Phoenix Aura",
        "values": {
            "interval": 100,
            "aoe_damage": 10,
        },
        "description_fn": lambda values: f"Emit a fiery aura dealing {values['aoe_damage']} damage per second to nearby enemies",
    },
    "chain_lightning": {
        "name": "Chain Lightning",
        "values": {
        },
        "description_fn": lambda values: f"Nearby enemies recieve a proportion of final weapon damage with diminishing effect.",
    },
    "cleave": {
        "name": "Cleave",
        "values": {
            "radius": 100
        },
        "description_fn": lambda values: "Deal splash damage to all nearby enemies based on final hit damage.",
    }
}

def handle_slime_shield_description(values):
    percent = values["damage_reduction_percent"]
    return f"Reduce damage taken from slimes by {percent}%"

def handle_slime_regen_description(values):
    interval = values["interval"]
    regen_percent = values["regen_percent"]

    seconds = interval / 1000
    percent = int(regen_percent * 100)
    return f"Heal {percent}% of max HP every {int(seconds)} seconds"

def handle_bone_thorns_description(values):
    reflect_percent = values["reflect_percent"]
    percent = int(reflect_percent * 100)
    return f"Reflect {percent}% damage back to attackers"
