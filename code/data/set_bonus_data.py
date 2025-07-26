SET_BONUS_DATA = {
    "slime_set": {
        "name": "Slime Set Bonus",
        "bonuses": {
            2: {
                "max_hp": 50,
                "extra_ability": "slime_shield"
            },
            3: {
                "max_hp": 100
            },
            4: {
                "max_hp": 200,
                "extra_ability": "slime_regen"
            },
        }
    },
    "bone_set": {
        "name": "Bone Set Bonus",
        "bonuses": {
            2: {
                "strength": 10,
                "extra_ability": "bone_thorns"
            },
            3: {
                "strength": 20
            },
            4: {
                "strength": 30
            },
            5: {
                "strength": 40,
                "extra_ability": "bone_thorns"
            },
        }
    },
    "phoenix_set": {
        "name": "Phoenix Set Bonus",
        "bonuses": {
            2: {
                "strength": 25,
            },
            3: {
                "speed": 10,
                "max_hp": 50,
            },
            4: {
                "extra_ability": "phoenix_aura",  # This is the signature bonus
                "strength": 50,
                "max_hp": 100,
            },
        },
    },
}