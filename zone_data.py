ZONE_DATA = [
    {
        "id": "starter_zone",
        "name": "Starter Zone",
        "size": 800,
        "safe": True,
        "enemy_spawn_table": [("slime", 1.0), ],
        "num_enemies": 5,
        "resource_node_spawn_table": [
            ("stone", 1.0)
        ],
        "num_resources": 3,
        "connections": {
            "left": "mining_camp",
            "right": "graveyard",
            "top": "forest",
        },
        "type": "combat",
    },
    {
        "id": "mining_camp",
        "name": "Mining Camp",
        "size": 1000,
        "safe": True,
        "enemy_spawn_table": [],
        "num_enemies": 0,
        "resource_node_spawn_table": [
            ("coal", 1.0), ("stone", 0.3), ("iron", 0.1)
        ],
        "num_resources": 20,
        "connections": {
            "right": "starter_zone",
            "down": "caverns",
        },
        "type": "mining",
        "requirements": {
            "mining": 2,
        },
    },
    {
        "id": "forest",
        "name": "Forest",
        "size": 1200,
        "safe": False,
        "enemy_spawn_table": [("slime", 1.0)],
        "num_enemies": 5,
        "resource_node_spawn_table": [
            ("tree", 1.0)
        ],
        "num_resources": 15,
        "connections": {
            "bottom": "starter_zone",
            "right": "oak_forest",
        },
        "type": "woodcutting",
        "requirements": {},
    },
    {
        "id": "oak_forest",
        "name": "Oak Forest",
        "size": 1200,
        "safe": False,
        "enemy_spawn_table": [("slime", 1.0)],
        "num_enemies": 5,
        "resource_node_spawn_table": [
            ("oak_tree", 1.0)
        ],
        "num_resources": 15,
        "connections": {
            "left": "forest",
            "top": "dark_thorn"
        },
        "type": "woodcutting",
        "requirements": {
            "woodcutting": 5
        },
    },
    {
        "id": "dark_thorn",
        "name": "Dark Thorn",
        "size": 800,
        "safe": False,
        "enemy_spawn_table": [("bark_fiend", 1.0)],
        "num_enemies": 10,
        "resource_node_spawn_table": [
            ("corrupted_tree", 1.0)
        ],
        "num_resources": 5,
        "connections": {
            "bottom": "oak_forest",
        },
        "type": "woodcutting",
        "requirements": {
            "combat": 10,
            "woodcutting": 10
        },
    },
    {
        "id": "caverns",
        "name": "Caverns",
        "size": 1600,
        "safe": False,
        "enemy_spawn_table": [("gloop", 1.0)],
        "num_enemies": 3,
        "resource_node_spawn_table": [
            ("iron", 0.8), ("stone", 0.5), ("coal", 0.5)
        ],
        "num_resources": 25,
        "connections": {
        },
        "type": "mining",
        "requirements": {
            "mining": 5
        }
    },
    {
        "id": "graveyard",
        "name": "Graveyard",
        "size": 1000,
        "safe": False,
        "enemy_spawn_table": [
            ("zombie", 1.0),
        ],
        "num_enemies": 25,
        "resource_node_spawn_table": [],
        "num_resources": 0,
        "connections": {
            "left": "starter_zone",
            "right": "spiders_den",
            "bottom": "crypts",
        },
        "type": "combat",
        "requirements": {"combat": 2}
    },
    {
        "id": "spiders_den",
        "name": "Spider's Den",
        "size": 1200,
        "safe": False,
        "enemy_spawn_table": [("spider", 1.0), ("red_spider", 0.2)],
        "num_enemies": 10,
        "resource_node_spawn_table": [ ("web_cocoon", 1.0) ],
        "num_resources": 10,
        "connections": {
            "left": "graveyard",
        },
        "type": "combat",
        "requirements": {"combat": 3 }
    },
    {
        "id": "crypts",
        "name": "The Crypts",
        "size": 1200,
        "safe": False,
        "enemy_spawn_table": [("ghoul", 0.5), ("zombie", 0.9)],
        "num_enemies": 15,
        "resource_node_spawn_table": [],
        "num_resources": 0,
        "connections": {
            "top": "graveyard",
            "right": "abandoned_tomb",
        },
        "type": "combat",
        "requirements": {"combat": 5}
    },
    {
        "id": "abandoned_tomb",
        "name": "Abandoned Tomb",
        "size": 600,
        "safe": False,
        "enemy_spawn_table": [("skeleton", 1.0), ("corrupted soul", 0.2)],
        "num_enemies": 10,
        "resource_node_spawn_table": [],
        "num_resources": 0,
        "connections": {
            "left": "crypts",
        },
        "type": "combat",
        "requirements": {"combat": 8 }
    },
    {
        "id": "phone_booth",
        "name": "The Phone Booth",
        "size": 200,
        "safe": False,
        "enemy_spawn_table": [("bombaclat", 1.0)],
        "num_enemies": 1,
        "resource_node_spawn_table": [],
        "num_resources": 0,
        "connections": {"top": "starter_zone"},
        "type": "boss",
        "requirements": {"combat": 10}
    },
]
