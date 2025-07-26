# task_data.py

from enemy_data import ENEMY_DATA
from recipe_data import CRAFTING_RECIPES
from item_data import ITEMS

def compute_difficulty_from_value(value):
    if value < 10:
        return "easy"
    elif value < 20:
        return "medium"
    elif value < 30:
        return "hard"
    elif value < 40:
        return "expert"
    elif value < 50:
        return "master"
    else:
        return "grandmaster"

TASK_DATA = []

# ----------------------
# Kill tasks (per enemy)
# ----------------------
for enemy_id, data in ENEMY_DATA.items():
    enemy_level = data.get("level", 1)
    difficulty = compute_difficulty_from_value(enemy_level)

    TASK_DATA.append({
        "id": f"kill_{enemy_id}_10",
        "name": f"{data['name']} Hunter",
        "description": f"Kill 10 {data['name']}s.",
        "task": {"type": "kill", "target": enemy_id, "count": 10},
        "rewards": {"coins": 100 * enemy_level},
        "requirements": {},
        "difficulty": difficulty
    })

# ----------------------
# Reach Level tasks (Combat, Mining, Woodcutting)
# ----------------------
for skill in ["combat", "mining", "woodcutting"]:
    for level in [5, 10, 15, 20]:
        difficulty = compute_difficulty_from_value(level)

        TASK_DATA.append({
            "id": f"{skill}_level_{level}",
            "name": f"{skill.title()} Adept {level}",
            "description": f"Reach {skill.title()} Level {level}.",
            "task": {"type": "reach_level", "target": skill, "count": level},
            "rewards": {"coins": 500 * level},
            "requirements": {},
            "difficulty": difficulty
        })

# ----------------------
# Craft tasks (per recipe)
# ----------------------
for recipe in CRAFTING_RECIPES:
    required_skills = recipe.get("requirements", {})
    skill_value = max(required_skills.values()) if required_skills else 1
    difficulty = compute_difficulty_from_value(skill_value)

    produces = recipe.get("produces", {})
    if produces:
        item_id = list(produces.keys())[0]
        TASK_DATA.append({
            "id": f"craft_{item_id}",
            "name": f"Craft {ITEMS.get(item_id, {}).get('name', item_id)}",
            "description": f"Craft {ITEMS.get(item_id, {}).get('name', item_id)}.",
            "task": {"type": "craft", "target": item_id, "count": 1},
            "rewards": {"coins": 500 * skill_value},
            "requirements": {},
            "difficulty": difficulty
        })
