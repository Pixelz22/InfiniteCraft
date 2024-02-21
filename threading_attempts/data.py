import os.path
import json

HISTORY_FILE = "history.json"
HISTORY: dict[str, int | list[any] | dict[str, int]] = {}
RECIPE_FILE = "recipes.json"
RECIPES: dict[str, list[str]] = {}
NULL_RECIPE_KEY = "%NULL%"
THREADS_FILE = "threads.json"
THREAD_DATA: list[tuple[int, int]] = []

def load():
    global HISTORY
    global RECIPES
    global THREAD_DATA
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

    # Load thread data from JSON file
    if os.path.exists(THREADS_FILE):
        with open(THREADS_FILE, "r") as fp:
            THREAD_DATA = json.load(fp)

def dump():
    # Save data after each level
    with open(HISTORY_FILE, "w") as fp:
        json.dump(HISTORY, fp, indent=4)
    with open(RECIPE_FILE, "w") as fp:
        json.dump(RECIPES, fp, indent=4)
    with open(THREADS_FILE, "w") as fp:
        json.dump(THREAD_DATA, fp, indent=4)
