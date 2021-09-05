import json
from collections import Counter
from datetime import timedelta
import math

raw_resources = [
    "ALO", "AMM", "AR", "AUO", "BER", "BOR", "BRM", "BTS", "CLI", "CUO", "F",
    "FEO", "GAL", "H", "H2O", "HAL", "HE", "HE3", "HEX", "LES", "LIO", "LST",
    "MAG", "MGS", "N", "NE", "O", "SCR", "SIO", "TAI", "TCO", "TIO", "TS", "ZIR"
]
recipes = {}
production = {}
inventory = Counter()
materials_needed = Counter()
multiple_recipe_remembered_choices = {}


def multiply_by_runs(materials_dict, multiply_factor):
    multiplied_dict = {}
    for material, amount in materials_dict.items():
        multiplied_dict[material] = amount * multiply_factor

    return multiplied_dict


def generate_normalized_recipe(recipe):
    normalized_recipe = {
        "name": recipe["RecipeName"],
        "building": recipe["BuildingTicker"],
        "inputs": {},
        "outputs": {},
        "time": timedelta(milliseconds=recipe["TimeMs"])
    }

    for recipe_inputs in recipe["Inputs"]:
        normalized_recipe["inputs"][recipe_inputs["Ticker"]] = recipe_inputs["Amount"]

    for recipe_outputs in recipe["Outputs"]:
        normalized_recipe["outputs"][recipe_outputs["Ticker"]] = recipe_outputs["Amount"]

    return normalized_recipe


def normalize_recipes_json(json_file):
    recipes_json = open(json_file, "r")
    raw_recipes = json.load(recipes_json)

    for raw_recipe in raw_recipes:
        for recipe_output in raw_recipe["Outputs"]:
            mat_ticker = recipe_output["Ticker"]
            normalized_recipe = generate_normalized_recipe(raw_recipe)

            if recipes.get(recipe_output["Ticker"]):
                recipes[mat_ticker]["recipes"].append(normalized_recipe)
                pass
            else:
                recipes[mat_ticker] = {
                    "recipes": [normalized_recipe]
                }


def add_recipe_to_production(recipe, runs, total_inputs, total_outputs):
    building = recipe["building"]
    total_recipe_time = recipe["time"] * runs

    if production.get(building):
        building_recipe = production[recipe["building"]]["recipes"].get(recipe["name"])

        if building_recipe:
            production[building]["recipes"][recipe["name"]]["inputs"].update(total_inputs)
            production[building]["recipes"][recipe["name"]]["outputs"].update(total_outputs)
            production[building]["recipes"][recipe["name"]]["runs"] += runs
            production[building]["recipes"][recipe["name"]]["time"] += total_recipe_time
        else:
            production[building]["recipes"][recipe["name"]] = {
                "inputs": Counter(total_inputs),
                "outputs": Counter(total_outputs),
                "runs": runs,
                "time": total_recipe_time
            }

        production[building]["total_time"] += total_recipe_time
    else:
        production[building] = {
            "recipes": {
                recipe["name"]: {
                    "inputs": Counter(total_inputs),
                    "outputs": Counter(total_outputs),
                    "runs": runs,
                    "time": total_recipe_time
                }
            },
            "total_time": total_recipe_time
        }


def select_recipe(material):
    material_recipes = recipes[material]["recipes"]

    if len(material_recipes) == 1:
        return material_recipes[0]
    else:
        if multiple_recipe_remembered_choices.get(material) is not None:
            return material_recipes[multiple_recipe_remembered_choices[material]]

        print("Select what recipe to use for {}:".format(material))
        for num, recipe in enumerate(material_recipes):
            print("{}: {}, Recipe Time: {}".format(num, recipe["name"], recipe["time"]))

        selected_recipe = int(input())
        multiple_recipe_remembered_choices[material] = selected_recipe
        return material_recipes[selected_recipe]


def execute_recipe(material, amount):
    if material in raw_resources:
        return

    recipe = select_recipe(material)
    runs_needed = math.ceil((amount - inventory.get(material, 0)) / recipe["outputs"][material])

    total_inputs = multiply_by_runs(recipe["inputs"], runs_needed)
    total_outputs = multiply_by_runs(recipe["outputs"], runs_needed)

    add_recipe_to_production(recipe, runs_needed, total_inputs, total_outputs)
    materials_needed.update(total_inputs)
    inventory.update(total_outputs)

    for mat_input, mat_amount in total_inputs.items():
        execute_recipe(mat_input, mat_amount)
        inventory.subtract({mat_input: mat_amount})

    # inventory.subtract(total_inputs)
    # print(runs_needed, total_outputs, total_inputs, recipe)
    # materials_needed.update(recipe['inputs'])


def pretty_print():
    for building in production:
        print("\n{} - Total Active Time: {}".format(building, production[building]["total_time"]))
        print("\trecipes")
        for recipe in production[building]["recipes"]:
            inputs_string, outputs_string = "", ""

            for material, amount in production[building]["recipes"][recipe]["inputs"].items():
                inputs_string = inputs_string + "{}:{}, ".format(material, amount)

            for material, amount in production[building]["recipes"][recipe]["outputs"].items():
                outputs_string = outputs_string + "{}:{}, ".format(material, amount)

            print("\t\tName: {}, Inputs: {} Outputs: {} Runs:{},  Total time: {}".format(
                recipe, inputs_string, outputs_string,
                production[building]["recipes"][recipe]["runs"],
                production[building]["recipes"][recipe]["time"]
            ))


if __name__ == "__main__":
    normalize_recipes_json("recipes.json")
    execute_recipe("GLASSSHIP", 1)
    print(materials_needed)
    print(inventory)
    print(production)
    pretty_print()
