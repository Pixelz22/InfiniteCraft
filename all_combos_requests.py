import requests
import json
import os.path
import time


HISTORY: dict[str, int | list[str]] = {}
RECIPES: dict[str, list[str]] = {}
LEVELS: dict[str, int] = {}
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


def all_combos(max_idx: int, min_idx=0, ) -> list[tuple[int, int]]:
    """
    Generates all combination of numbers below max_idx.
    Ignores all combinations in which both numbers are below min_idx.
    """
    combos = []
    for i in range(0, max_idx):
        for j in range(max(i, min_idx), max_idx):
            combos.append((i, j))
    return combos


def produce_all_combinations(level: int, ignore_below=0, sleep=0.0) -> int:
    batch_size = len(HISTORY["elements"])
    combos = all_combos(batch_size, min_idx=ignore_below)

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

        if recipe_key not in RECIPES[result_key]:
            RECIPES[result_key].append(recipe_key)

        if result_key not in HISTORY["elements"]:
            HISTORY["elements"].append(result_key)

        if result_json["result"] not in LEVELS:
            LEVELS[result_json["result"]] = level

        if result_json["isNew"]:
            with open("newRecipes.txt", "a") as fp:
                fp.write(result_key + "\n")

        time.sleep(sleep)

    return batch_size


if __name__ == "__main__":
    # Load history from JSON file
    if os.path.exists("history.json"):
        with open("history.json", "r") as fp:
            HISTORY = json.load(fp)

    # Load recipes from JSON file
    if os.path.exists("recipes.json"):
        with open("recipes.json", "r") as fp:
            RECIPES = json.load(fp)

    # Load levels from JSON file
    if os.path.exists("levels.json"):
        with open("levels.json", "r") as fp:
            LEVELS = json.load(fp)

    last_batch_size = HISTORY["last_batch_size"]  # Keeps track of the highest index we haven't checked
    level = HISTORY["last_level"]  # Keeps track of our current level
    try:
        # Main Loop
        SESSION = requests.session()
        SESSION.headers = rHEADERS

        while True:
            c = input("Continue? ")
            if c == "N" or c == "n":
                break

            level += 1
            start = time.time_ns()
            last_batch_size = produce_all_combinations(level, ignore_below=last_batch_size, sleep=0.1)
            duration = (time.time_ns() - start) / 1000000000
            print(f"Level {level}: Duration - {duration} s;")
    finally:
        HISTORY["last_level"] = level
        HISTORY["last_batch_size"] = last_batch_size
        with open("history.json", "w") as fp:
            json.dump(HISTORY, fp, indent=4)
        with open("recipes.json", "w") as fp:
            json.dump(RECIPES, fp, indent=4)
        with open("levels.json", "w") as fp:
            json.dump(LEVELS, fp, indent=4)
