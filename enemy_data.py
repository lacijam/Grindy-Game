from constants import *

ENEMY_DATA = {
    "slime": {
        "name": "Slime",
        "type": "mob",
        "size": 20,
        "colour": (0, 255, 0),
        "sounds": {
            "hit": "slime_hit",
        },
        "level": 3,
        "hp": 50,
        "damage": 10,
        "speed": 100,
        "weight": 1.1,
        "xp": 10,
        "coins": 5,
        "drop_table": {
            "common": [("slime_juice", 0.7, (1, 3))],
            "rare": [("wooden_axe", 0.01), ("wooden_pickaxe", 0.01)],
            "epic": [("slime_core", 0.003)],
            "mythic": [("slime_soul", 0.00001)],
        },
        "beastiary": {
            "max_level": 12,
            "thresholds": [1, 10, 50, 100, 200, 500, 1000, 2500, 5000, 10000, 25000, 50000]
        }
    },
    "tree_fang": {
        "name": "Tree Fang",
        "type": "mob",
        "size": 25,
        "colour": (150, 255, 150),
        "sounds": {
            "hit": "hard_hit",
        },
        "level": 12,
        "hp": 150,
        "damage": 60,
        "speed": 150,
        "weight": 1.4,
        "xp": 25,
        "coins": 5,
        "drop_table": {
            "rare": [("ancient_bark", 0.05, (1, 3))],
            "epic": [("axe_of_thorns", 0.002)],
            "mythic": [("tree_soul", 0.00001)],
        },
        "beastiary": {
            "max_level": 12,
            "thresholds": [1, 10, 50, 100, 200, 500, 1000, 2500, 5000, 10000, 25000, 50000]
        }
    },
    "zombie": {
        "name": "Zombie",
        "type": "mob",
        "size": 30,
        "colour": (100, 200, 100),
        "sounds": {
            "hit": "zombie_hit",
        },
        "level": 5,
        "hp": 100,
        "damage": 20,
        "speed": 60,
        "weight": 1.7,
        "xp": 15,
        "coins": 5,
        "drop_table": {
            "common": [("rotten_flesh", 1.0, (1, 3))],
            "rare": [("leather_helmet", 0.015), ("leather_chestplate", 0.015), ("leather_boots", 0.015)],
            "mythic": [("zombie_soul", 0.00001)],
        },
        "beastiary": {
            "max_level": 12,
            "thresholds": [1, 10, 50, 100, 200, 500, 1000, 2500, 5000, 10000, 25000, 50000]
        }
    },
    "spider": {
        "name": "Spider",
        "type": "mob",
        "size": 24,
        "colour": (30, 30, 30),
        "level": 8,
        "hp": 200,
        "damage": 25,
        "speed": 120,
        "weight": 1.2,
        "xp": 20,
        "coins": 50,
        "drop_table": {
            "common": [("silk", 0.75, (1, 2))],
            "epic": [("silk_striders", 0.005)],
            "mythic": [("silk_soul", 0.00001)],
        },
        "beastiary": {
            "max_level": 12,
            "thresholds": [1, 10, 50, 100, 200, 500, 1000, 2500, 5000, 10000, 25000, 50000]
        }
    },
    "red_spider": {
        "name": "Red Spider",
        "type": "mob",
        "size": 32,
        "colour": (100, 30, 30),
        "level": 15,
        "hp": 400,
        "damage": 80,
        "speed": 140,
        "weight": 1.6,
        "xp": 30,
        "coins": 70,
        "drop_table": {
            "common": [("silk", 0.75, (3, 5))],
            "epic": [("fang_dagger", 0.01)],
            "mythic": [("silk_soul", 0.00002)],
        },
        "beastiary": {
            "max_level": 12,
            "thresholds": [1, 10, 50, 100, 200, 500, 1000, 2500, 5000, 10000, 25000, 50000]
        }
    },
    "skeleton": {
        "name": "Skeleton",
        "type": "mob",
        "size": 28,
        "colour": (240, 240, 240),
        "sounds": {
            "hit": "skeleton_hit",
        },
        "level": 7,
        "hp": 150,
        "damage": 15,
        "speed": 90,
        "weight": 1.0,
        "xp": 20,
        "coins": 30,
        "drop_table": {
            "common": [("bone", 0.6, (1, 2))],
            "rare": [("bone_plate", 0.01)],
            "mythic": [("bone_soul", 0.00001)],
        },
        "beastiary": {
            "max_level": 12,
            "thresholds": [1, 10, 50, 100, 200, 500, 1000, 2500, 5000, 10000, 25000, 50000]
        }
    },
    "ghoul": {
        "name": "Ghoul",
        "type": "mob",
        "size": 25,
        "colour": (130, 200, 100),
        "sounds": {
            "hit": "zombie_hit",
        },
        "level": 15,
        "hp": 400,
        "damage": 75,
        "speed": 100,
        "weight": 1.3,
        "xp": 30,
        "coins": 15,
        "drop_table": {
            "common": [("rotten_flesh", 1.0, (1, 3))],
            "epic": [("ghoulish_greaves", 0.005)],
            "mythic": [],
        },
        "beastiary": {
            "max_level": 12,
            "thresholds": [1, 10, 50, 100, 200, 500, 1000, 2500, 5000, 10000, 25000, 50000]
        }
    },
    "corrupted_soul": {
        "name": "Corrupted Soul",
        "type": "mob",
        "size": 30,
        "colour": (130, 150, 100),
        "sounds": {
            "hit": "zombie_hit",
        },
        "level": 30,
        "hp": 1000,
        "damage": 150,
        "speed": 80,
        "weight": 1.5,
        "xp": 40,
        "coins": 80,
        "drop_table": {
            "common": [("rotten_flesh", 1.0, (1, 3))],
            "rare": [],
            "epic": ["corrupted_essence", 0.01],
            "mythic": [],
        },
        "beastiary": {
            "max_level": 10,
            "thresholds": [1, 10, 50, 100, 200, 500, 1000, 2500, 5000, 10000, 25000, 50000]
        }
    },
    "bombaclat": {
        "name": "BOMBACLAT",
        "type": "boss",
        "size": 64,
        "colour": (180, 0, 255),
        "sounds": {
            "hit": "slime_hit",
        },
        "level": 100,
        "damage": 500,
        "hp": 5000,
        "speed": 200,
        "weight": 8.0,
        "xp": 200,
        "coins": 500,
        "drop_table": {
            "common": [],
        },
        "beastiary": {
            "max_level": 1,
            "thresholds": [1]
        },
        "subtitle": "Prodigee of Monkey Goggins"
    }
}
