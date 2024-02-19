import requests
import json
import os.path
import time
import proxy

from utilities import DelayedKeyboardInterrupt, to_percent

HISTORY_FILE = "../history.json"
HISTORY: dict[str, int | list[any] | dict[str, int]] = {}
RECIPE_FILE = "../recipes-1.json"
RECIPES: dict[str, list[str]] = {}
NULL_RECIPE_KEY = "%NULL%"

SESSION: requests.Session | None = None
# SESSIONS: list[requests.Session] | None = None

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


def process_partial_batch(batch: list[tuple[int, int]], sleep=0.0):
    for i, combo in enumerate(batch):
        e1 = HISTORY["elements"][combo[0]]
        e2 = HISTORY["elements"][combo[1]]
        recipe_key = e1 + ";" + e2

        result_json = combine(e1, e2)
        result_key = result_json["result"]

        if result_key == "Nothing":
            RECIPES[NULL_RECIPE_KEY].append(recipe_key)
            print(f"Batch%: {to_percent(i / len(batch))}% -- NULL RECIPE: {e1} + {e2}")
            continue

        print(f"Batch%: {to_percent(i / len(batch))}% -- {e1} + {e2} = {result_key}")

        # Update recipes
        if result_key not in RECIPES:
            RECIPES[result_key] = [recipe_key]
        elif recipe_key not in RECIPES[result_key]:
            RECIPES[result_key].append(recipe_key)

        # Update our history
        if result_key not in HISTORY["elements"]:
            HISTORY["elements"].append(result_key)

        if result_key not in HISTORY["levels"]:
            HISTORY["levels"][result_key] = HISTORY["level"]

        # Keep track of new discoveries
        if result_json["isNew"]:
            print(f"NEW DISCOVERY: {e1} + {e2} = {result_key}")
            with open("../newRecipes.txt", "a") as fp:
                fp.write(result_key + "\n")

        HISTORY["last_combo"] = list(combo)
        time.sleep(sleep)


def progress(sleep=0.0):
    last_batch_partial = []

    # Process batch
    for j in range(HISTORY["last_combo"][1], HISTORY["batch_size"]):
        last_batch_partial.append((HISTORY["last_combo"][0], j))  # Only check ones that came after our last combo

    for i in range(HISTORY["last_combo"][0] + 1, HISTORY["batch_size"]):
        for j in range(max(i, HISTORY["last_batch_size"]), HISTORY["batch_size"]):
            last_batch_partial.append((i, j))  # Only check ones that came after our last combo

    process_partial_batch(last_batch_partial, sleep=sleep)

    with DelayedKeyboardInterrupt():  # Ensures we don't accidentally exit the code while updating crucial data
        HISTORY["last_batch_size"] = HISTORY["batch_size"]
        HISTORY["batch_size"] = len(HISTORY["elements"])
        HISTORY["level"] += 1
        HISTORY["last_combo"] = [0, HISTORY["last_batch_size"]]


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

    # Inititalize proxies
    proxy.update_proxies()
    print("Proxies initialized")
    # SESSIONS = proxy.get_proxy_sessions(rHEADERS)
    SESSION = requests.session()
    SESSION.headers = rHEADERS
    print("Sessions initialized")

    try:

        while True:
            start = time.time_ns()
            progress(sleep=0.125)
            duration = (time.time_ns() - start) / 1000000000
            print(f"LEVEL {HISTORY['level'] - 1}: Duration - {duration} s; "
                  f"Found {HISTORY['batch_size'] - HISTORY['last_batch_size']} new crafts")
            print("---------------")

            # Save data after each level
            with open(HISTORY_FILE, "w") as fp:
                json.dump(HISTORY, fp, indent=4)
            with open(RECIPE_FILE, "w") as fp:
                json.dump(RECIPES, fp, indent=4)

    finally:
        SESSION.close()
        # for s in SESSIONS:
        #    s.close()
        with open(HISTORY_FILE, "w") as fp:
            json.dump(HISTORY, fp, indent=4)
        with open(RECIPE_FILE, "w") as fp:
            json.dump(RECIPES, fp, indent=4)
