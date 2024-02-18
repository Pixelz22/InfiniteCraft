import threading
import time
import selenium.webdriver.remote.webelement
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.support.wait import WebDriverWait

DRIVER: webdriver.Chrome | None = None

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
    initial_elements = DRIVER.find_elements(By.XPATH, "//div[@class='mobile-items']//div[@class='item']")

    combos = all_combos(len(initial_elements), min_idx=ignore_below)

    for combo in combos:
        initial_elements[combo[0]].click()
        initial_elements[combo[1]].click()
        time.sleep(0.01)

    return len(initial_elements)


def produce_all_combos_threading(ignore_below=0) -> int:
    initial_elements = DRIVER.find_elements(By.XPATH, "//div[@class='mobile-items']//div[@class='item']")

    combos = all_combos(len(initial_elements), min_idx=ignore_below)

    split = len(combos) // 2

    t1 = threading.Thread(target=pact_helper, args=(initial_elements, combos[:split]))
    t2 = threading.Thread(target=pact_helper, args=(initial_elements, combos[split:]))

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    return len(initial_elements)


def pact_helper(initial_elements, combos) -> None:
    for combo in combos:
        initial_elements[combo[0]].click()
        initial_elements[combo[1]].click()
        time.sleep(0.01)


if __name__ == "__main__":
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
    while True:
        c = input("Continue?")
        if c == "N" or c == "n":
            break
        ignore = produce_all_combinations(ignore_below=ignore)

    DRIVER.quit()
