CRAFTING_RECIPES = [
    {
        "name": "Refined Iron",
        "category": "resource",
        "requires": {"iron": 10, "coal": 5},
        "produces": {"refined_iron": 1},
        "requirements": { "mining": 5 },
    },
    {
        "name": "Slime Core",
        "category": "resource",
        "requires": {"slime_juice": 150},
        "produces": {"slime_core": 1},
        "requirements": { "combat": 2 },
    },
    {
        "name": "Iron Maul",
        "category": "Weapon",
        "requires": {"wood": 10, "refined_iron": 1},
        "produces": {"iron_maul": 1},
        "requirements": { "combat": 6, "mining": 5}
    },
    {
        "name": "Iron Axe",
        "category": "Tool",
        "requires": {"wood": 15, "refined_iron": 1 },
        "produces": {"iron_axe": 1},
        "requirements": { "woodcutting": 5}
    },
    {
        "name": "Corrupted Axe",
        "category": "Tool",
        "requires": {"corrupted_essence": 5, "refined_iron": 50, "corrupted_wood": 50 },
        "produces": {"corrupted_axe": 1},
        "requirements": { "woodcutting": 12 }
    },
    {
        "name": "Iron Pickaxe",
        "category": "Tool",
        "requires": {"wood": 15, "refined_iron": 5 },
        "produces": {"iron_pickaxe": 1},
        "requirements": { "mining": 5 }
    },
    {
        "name": "Globbulite Pickaxe",
        "category": "Tool",
        "requires": {"wood": 15, "refined_iron": 25, "slime_core": 10 },
        "produces": {"globbulite_pickaxe": 1},
        "requirements": { "mining": 12 }
    }
]