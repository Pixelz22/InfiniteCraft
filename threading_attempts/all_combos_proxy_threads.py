import math

import requests
import data
import time
import proxy
from custom_threads import CrafterThread, IPBlockException
from utilities import DelayedKeyboardInterrupt, verbose_sleep

SESSION: requests.Session | None = None
SESSIONS: list[requests.Session] | None = None

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
            for combo in thread.recipes:
                if combo not in data.RECIPES[recipe]:
                    data.RECIPES[recipe].append(combo)

def regenerate_thread_data(num_threads):
    new_threads: list[dict[str, any]] = []

    min_thread_size = (data.HISTORY["batch_size"] - data.HISTORY["last_batch_size"]) // num_threads
    while min_thread_size < 1:  # Lower the number of threads if we have too many
        num_threads -= 1
        min_thread_size = (data.HISTORY["batch_size"] - data.HISTORY["last_batch_size"]) // num_threads

    # Prepare the next set of thread data to be processed
    for i in range(data.HISTORY["last_batch_size"], data.HISTORY["batch_size"] - min_thread_size + 1,
                   min_thread_size):
        min_idx = i
        if i + 2 * min_thread_size > data.HISTORY["batch_size"]:
            max_idx = data.HISTORY["batch_size"]
        else:
            max_idx = i + min_thread_size

        start_combo = 0, min_idx

        new_threads.append({"min": min_idx, "max": max_idx, "start": start_combo})
    data.THREAD_DATA = new_threads


def evolve(num_threads=1, sleep=0.0):
    if len(data.THREAD_DATA) == 0:  # Quick catch in case threads were deleted
        regenerate_thread_data(num_threads)

    threads = []
    for i, thread_data in enumerate(data.THREAD_DATA):
        t = CrafterThread(SESSION, data.HISTORY, thread_data["start"],
                          thread_data["min"], thread_data["max"], sleep=sleep)
        t.start()
        threads.append(t)

    # Rejoin with threads once they finish
    try:
        for t in threads:
            while t.is_alive():  # Can't use straight up t.join(), cause then it doesn't let KeyboardInterrupts through
                t.join(0.1)
            store_thread_results(t)
    except BaseException as e:
        print("Exception raised while processing threads, closing threads safely...")
        new_thread_data = []
        for i, t in enumerate(threads):
            t.kill()  # Safely kill threads
            t.join(ignore_exceptions=True)
            store_thread_results(t)
            if not t.success:  # Store thread progress so we can restart at same place
                new_thread_data.append({"min": t.min_idx, "max": t.max_idx, "start": t.start_combo})
        data.THREAD_DATA = new_thread_data
        data.dump()
        print("Threads closed safely")
        raise e

    with DelayedKeyboardInterrupt():  # Ensures we don't accidentally exit the code while updating crucial data
        data.HISTORY["last_batch_size"] = data.HISTORY["batch_size"]
        data.HISTORY["batch_size"] = len(data.HISTORY["elements"])
        data.HISTORY["level"] += 1
        regenerate_thread_data(num_threads)


if __name__ == "__main__":
    data.load()

    # Initialize proxies
    # proxy.update_proxies()
    print("Proxies initialized")
    # SESSIONS = proxy.get_proxy_sessions(rHEADERS)
    SESSION = requests.session()
    SESSION.headers = rHEADERS
    print("Sessions initialized")

    try:

        while True:
            try:
                start = time.time()
                evolve(num_threads=5, sleep=1)
                duration = time.time() - start
                print(f"LEVEL {data.HISTORY['level'] - 1}: Duration - {duration} s; "
                      f"Found {data.HISTORY['batch_size'] - data.HISTORY['last_batch_size']} new crafts")
                print("---------------")
                data.dump()
            except IPBlockException as ipe:
                print(str(ipe) + " Beginning sleep...")
                verbose_sleep(ipe.retry_time, 5 * 60)
                print("Sleep over, continuing...")

    finally:
        # for s in SESSIONS:
        #    s.close()
        SESSION.close()
        data.dump()
        print("Data saved")
