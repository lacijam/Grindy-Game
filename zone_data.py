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
            "top": "forest",
            "right": "graveyard",
        },
        "type": "combat",
    },
    {
        "id": "forest",
        "name": "Forest",
        "size": 1200,
        "safe": True,
        "enemy_spawn_table": [("slime", 1.0), ],
        "num_enemies": 25,
        "resource_node_spawn_table": [
        ],
        "num_resources": 0,
        "connections": {
            "top": "deep_hollow",
        },
        "type": "combat",
    },
    {
        "id": "deep_hollow",
        "name": "Deep Hollow",
        "size": 800,
        "safe": True,
        "enemy_spawn_table": [("tree_fangs", 1.0), ],
        "num_enemies": 10,
        "resource_node_spawn_table": [
        ],
        "num_resources": 0,
        "connections": {
        },
        "type": "combat",
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
]
