import sys

import requests
import json
import os.path
import time

HISTORY_FILE = "history.json"
HISTORY: dict[str, int | list[str] | list[int]] = {}
RECIPE_FILE = "recipes-1.json"
RECIPES: dict[str, list[str]] = {}
NULL_RECIPE_KEY = "%NULL%"

SESSION: requests.sessions.Session | None = None

rHEADERS = {
    'User-Agent': 'BocketBot',
    'Accept': '/',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://neal.fun/infinite-craft/',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-GPC': '1',
}

def combine(one: str, two: str):

    params = {
        'first': one,
        'second': two,
    }

    response = SESSION.get('https://neal.fun/api/infinite-craft/pair', params=params)

    return json.loads(response.content.decode('utf-8'))


def all_combos() -> list[tuple[int, int]]:
    """
    Generates all combination of numbers below max_idx.
    Ignores all combinations in which both numbers are below min_idx.
    """
    combos = []
    batch_size = len(HISTORY["elements"])

    # Finish last batch first
    for j in range(HISTORY["last_combo"][1], HISTORY["last_batch_size"]):
        combos.append((HISTORY["last_combo"][0], j))  # Only check ones that came after our last combo

    for i in range(HISTORY["last_combo"][0] + 1, HISTORY["last_batch_size"]):
        for j in range(i, HISTORY["last_batch_size"]):
            combos.append((i, j))  # Only check ones that came after our last combo

    # Now start on the next level
    for i in range(0, batch_size):
        for j in range(max(i, HISTORY["last_batch_size"]), batch_size):
            combos.append((i, j))
    return combos


def produce_all_combinations(sleep=0.0) -> int:
    batch_size = len(HISTORY["elements"])
    combos = all_combos()
    HISTORY["last_batch_size"] = batch_size

    for combo in combos:
        e1 = HISTORY["elements"][combo[0]]
        e2 = HISTORY["elements"][combo[1]]
        recipe_key = e1 + ";" + e2

        result_json = combine(e1, e2)
        result_key = result_json["result"]

        if result_key == "Nothing":
            RECIPES[NULL_RECIPE_KEY].append(recipe_key)
            print(f"NULL RECIPE: {e1} + {e2}")
            continue

        print(f"{e1} + {e2} = {result_key}")

        # Update recipes
        if result_key not in RECIPES:
            RECIPES[result_key] = [recipe_key]
        elif recipe_key not in RECIPES[result_key]:
            RECIPES[result_key].append(recipe_key)

        # Update our history
        if result_key not in HISTORY["elements"]:
            HISTORY["elements"].append(result_key)

        # Keep track of new discoveries
        if result_json["isNew"]:
            print(f"NEW DISCOVERY: {e1} + {e2} = {result_key}")
            with open("newRecipes.txt", "a") as fp:
                fp.write(result_key + "\n")

        HISTORY["last_combo"] = list(combo)
        time.sleep(sleep)

    return batch_size


if __name__ == "__main__":
    # Load history from JSON file
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as fp:
            HISTORY = json.load(fp)

    # Load recipes from JSON file
    if os.path.exists(RECIPE_FILE):
        with open(RECIPE_FILE, "r") as fp:
            RECIPES = json.load(fp)
            if NULL_RECIPE_KEY not in RECIPES:
                RECIPES[NULL_RECIPE_KEY] = []

    try:
        SESSION = requests.session()
        SESSION.headers = rHEADERS

        start = time.time_ns()
        produce_all_combinations(sleep=0.15)
        duration = (time.time_ns() - start) / 1000000000
        print(f"Duration - {duration} s;")

    finally:
        SESSION.close()
        with open(HISTORY_FILE, "w") as fp:
            json.dump(HISTORY, fp, indent=4)
        with open(RECIPE_FILE, "w") as fp:
            json.dump(RECIPES, fp, indent=4)
