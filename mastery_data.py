from recipe_data import CRAFTING_RECIPES
from item_data import ITEMS

def autogenerate_mastery_contributions():
    table = {}

    for recipe in CRAFTING_RECIPES:
        produces = recipe.get("produces", {})
        requires = recipe.get("requires", {})

        if len(produces) != 1:
            continue

        if len(requires) != 1:
            continue

        output_id = next(iter(produces))
        output_qty = produces[output_id]

        input_id, input_qty = next(iter(requires.items()))
        if "max_mastery_level" not in ITEMS.get(input_id, {}):
            continue

        contribution_per_output = input_qty // output_qty

        table[output_id] = {input_id: contribution_per_output}

    return table

def get_mastery_contribution_for_item(item_id):
    return MASTERY_CONTRIBUTION_TABLE.get(item_id, {})

# Generate at load time
MASTERY_CONTRIBUTION_TABLE = autogenerate_mastery_contributions()