import threading
import time
import selenium.webdriver.remote.webelement
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common import NoSuchElementException, ElementNotInteractableException, ElementClickInterceptedException
from selenium.webdriver.support.wait import WebDriverWait
import json

DRIVER: webdriver.Chrome | None = None

RECIPES: dict[str, list[str]] = {}

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


def produce_all_combinations(ignore_below=0) -> int:
    ignored_recipes = set()
    initial_elements = DRIVER.find_elements(By.XPATH, "//div[@class='mobile-items']//div[@class='item']")

    combos = all_combos(len(initial_elements), min_idx=ignore_below)
    wait = WebDriverWait(DRIVER, timeout=5, poll_frequency=0.01,
                         ignored_exceptions=[ElementNotInteractableException, ElementClickInterceptedException])

    for combo in combos:
        e1 = initial_elements[combo[0]]
        e2 = initial_elements[combo[1]]
        recipe_key = e1.text.partition(" ")[2] + ";" + e2.text.partition(" ")[2]
        if recipe_key in ignored_recipes:
            continue

        wait.until(lambda d: e1.click() or True)
        wait.until(lambda d: e2.click() or True)
        # TODO: Need an efficient way of detecting if there was a new result,
        # then need to find that result and use it to add to our recipes list.
        time.sleep(0.15)

    return len(initial_elements)


if __name__ == "__main__":
    with open("recipes.json", "r") as fp:
        RECIPES = json.load(fp)

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

    DRIVER.quit()
