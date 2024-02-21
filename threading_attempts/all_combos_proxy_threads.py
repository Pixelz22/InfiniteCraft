import math
import sys
import warnings
import requests
import data
import time
import proxy
from custom_threads import CrafterThread
from utilities import DelayedKeyboardInterrupt

SESSION: requests.Session | None = None
SESSIONS: list[requests.Session] | None = None


def store_thread_results(thread: CrafterThread):
    for element in thread.crafted:
        if element not in data.HISTORY["elements"]:
            data.HISTORY["elements"].append(element)

    for element in thread.levels:
        if element not in data.HISTORY["levels"]:
            data.HISTORY["levels"][element] = thread.levels[element]

    for recipe in thread.recipes:
        if recipe not in data.RECIPES:
            data.RECIPES[recipe] = thread.recipes[recipe]
        else:
            for combo in thread.recipes[recipe]:
                if combo not in data.RECIPES[recipe]:
                    data.RECIPES[recipe].append(combo)

    with open("../newRecipes.txt", 'a') as fp:
        for element in thread.new_recipes:
            fp.write(element)

def generate_combos() -> list[tuple[int, int]]:
    combos = []
    for i in range(data.HISTORY["batch_size"]):
        for j in range(max(i, data.HISTORY["last_batch_size"]), data.HISTORY["batch_size"]):
            combos.append((i, j))
    return combos


def evolve(num_threads=1, delay=0.0):
    if len(data.THREAD_DATA) == 0:
        data.THREAD_DATA = generate_combos()

    # Create threads
    max_thread_size = math.ceil(len(data.THREAD_DATA) / num_threads)
    threads = []
    mini_batch = []
    for combo in data.THREAD_DATA:
        mini_batch.append(tuple(combo))
        if len(mini_batch) >= max_thread_size:
            t = CrafterThread(data.HISTORY, mini_batch, delay=delay, id=len(threads))
            t.start()
            threads.append(t)
            mini_batch = []

    if len(mini_batch) > 0:
        t = CrafterThread(data.HISTORY, mini_batch, delay=delay, id=len(threads))
        t.start()
        threads.append(t)

    # Rejoin with threads once they finish
    new_thread_data: list[tuple[int, int]] = []
    first_open_thread = 0
    try:
        for i, t in enumerate(threads):
            while t.is_alive():  # Can't use straight up t.join(), cause then it doesn't let KeyboardInterrupts through
                t.join(0.1)
            store_thread_results(t)
            if not t.success:  # If thread failed, save its progress for next time
                t.dump_combos(new_thread_data)
            first_open_thread += 1  # Increment this counter so we don't try to close an already closed thread
            print(f"THREAD #{t.ID} CLOSED")
    except BaseException as e:
        print("Exception raised while processing threads, closing threads safely...")
        for i in range(first_open_thread, len(threads)):  # Start closing the open threads
            t = threads[i]
            t.kill()  # Safely kill threads
            t.join(ignore_exceptions=True)
            store_thread_results(t)
            if not t.success:  # Store thread progress so we can restart at same place
                t.dump_combos(new_thread_data)
            print(f"THREAD #{t.ID} CLOSED")
        data.THREAD_DATA = new_thread_data
        data.dump()
        print("Threads closed safely")
        raise e

    # Check if any of the threads exited unsuccessfully
    if len(new_thread_data) != 0:
        data.THREAD_DATA = new_thread_data
        data.dump()
        print("One of the threads failed. Please try again later.")
        sys.exit(1)

    # Save data
    with DelayedKeyboardInterrupt():  # Ensures we don't accidentally exit the code while updating crucial data
        data.HISTORY["last_batch_size"] = data.HISTORY["batch_size"]
        data.HISTORY["batch_size"] = len(data.HISTORY["elements"])
        data.HISTORY["level"] += 1
        data.THREAD_DATA = generate_combos()
        data.dump()


if __name__ == "__main__":
    data.load()

    # Initialize proxies
    num_proxies = 1
    try:
        warnings.filterwarnings("ignore")
        num_proxies = proxy.update_proxies()
        print("Proxies initialized")
    except:
        print("Proxies failed")

    try:

        while True:
            start = time.time()
            evolve(num_threads=50, delay=0.15)
            duration = time.time() - start
            print(f"LEVEL {data.HISTORY['level'] - 1}: Duration - {duration} s; "
                  f"Found {data.HISTORY['batch_size'] - data.HISTORY['last_batch_size']} new crafts")
            print("---------------")
    except KeyboardInterrupt:
        pass
    finally:
        data.dump()
        print("Data saved")
