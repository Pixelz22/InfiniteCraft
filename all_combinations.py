import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common import NoSuchElementException, ElementNotInteractableException, ElementClickInterceptedException
from selenium.common import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
import json
import os.path

DRIVER: webdriver.Chrome | None = None

RECIPES: dict[str, list[str]] = {}
NULL_RECIPE_KEY = "%NULL%"

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


IGNORED_RECIPES = set()
def produce_all_combinations(ignore_below=0) -> int:
    global IGNORED_RECIPES

    item_parent = DRIVER.find_element(By.CLASS_NAME, "mobile-items")
    initial_elements = item_parent.find_elements(By.CLASS_NAME, "item")

    combos = all_combos(len(initial_elements), min_idx=ignore_below)
    wait = WebDriverWait(DRIVER, timeout=1, poll_frequency=0.01,
                         ignored_exceptions=[NoSuchElementException, ElementNotInteractableException,
                                             ElementClickInterceptedException])

    for combo in combos:
        e1 = initial_elements[combo[0]]
        e2 = initial_elements[combo[1]]
        recipe_key = e1.text.partition("\n")[2] + ";" + e2.text.partition("\n")[2]
        if recipe_key in IGNORED_RECIPES:
            continue

        wait.until(lambda d: e1.click() or True)
        wait.until(lambda d: e2.click() or True)

        try:
            wait.until(lambda d: item_parent.find_element(By.CLASS_NAME, "item-crafted-mobile") or True)

            # If we find the resulting recipe, add it to our list
            crafted = item_parent.find_element(By.CLASS_NAME, "item-crafted-mobile")
            crafted_key = crafted.text.partition("\n")[2]
            print(recipe_key + " = " + crafted_key)

            if crafted_key not in RECIPES:
                RECIPES[crafted_key] = [recipe_key]
            elif recipe_key not in RECIPES[crafted_key]:
                RECIPES[crafted_key].append(recipe_key)
                IGNORED_RECIPES.add(recipe_key)  # Only need to add this key, not re-add whole list
            else:
                IGNORED_RECIPES.update(RECIPES[crafted_key])  # Now that we've found a recipe, ignore other versions

        except TimeoutException:
            print("NEW NULL RECIPE DISCOVERED: " + recipe_key)
            RECIPES[NULL_RECIPE_KEY].append(recipe_key)  # Recipe doesn't craft anything, add it to the null list

    return len(initial_elements)


if __name__ == "__main__":
    if os.path.exists("recipes.json"):
        with open("recipes.json", "r") as fp:
            RECIPES = json.load(fp)
            if NULL_RECIPE_KEY in RECIPES:  # Automatically ignore null recipes
                IGNORED_RECIPES.update(RECIPES[NULL_RECIPE_KEY])
            else:
                RECIPES[NULL_RECIPE_KEY] = []  # Initialize it if it doesn't exist
    try:
        options = Options()
        DRIVER = webdriver.Chrome(options)

        DRIVER.implicitly_wait(1)

        DRIVER.get("https://neal.fun/infinite-craft/")

        try:
            sidebar = DRIVER.find_element(By.CLASS_NAME, "sidebar")

            DRIVER.set_window_size(0, 1000)
        except NoSuchElementException:
            print("we're in small mode")

        ignore = 0
        level = 0
        while True:
            c = input("Continue? ")
            if c == "N" or c == "n":
                break

            level += 1
            start = time.time_ns()
            ignore = produce_all_combinations(ignore_below=ignore)
            duration = (time.time_ns() - start) / 1000000000
            print(f"Level {level}: Duration - {duration} s;")
    finally:
        DRIVER.quit()
        with open("recipes.json", "w") as fp:
            json.dump(RECIPES, fp, indent=4)
