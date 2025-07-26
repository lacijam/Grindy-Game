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
            "right": "graveyard",
            "left": "spiders_den",
            "top": "crypts",
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
            "right": "starter_zone",
        },
        "type": "combat",
        "requirements": {"combat": 3 }
    },
    {
        "id": "crypts",
        "name": "The Crypts",
        "size": 1200,
        "safe": False,
        "enemy_spawn_table": [("skeleton", 0.9), ("zombie", 0.1)],
        "num_enemies": 15,
        "resource_node_spawn_table": [],
        "num_resources": 0,
        "connections": {
            "bottom": "starter_zone",
        },
        "type": "combat",
        "requirements": {"combat": 5}
    },
]
