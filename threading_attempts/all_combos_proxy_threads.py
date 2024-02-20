import requests
import data
import time
import proxy
from custom_threads import CrafterThread
from utilities import DelayedKeyboardInterrupt

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


def evolve(num_threads=1, sleep=0.0):

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
    except Exception as e:
        print("Exception raised while processing threads, closing threads safely...")
        for i, t in enumerate(threads):
            t.kill()  # Safely kill threads
            t.join()
            store_thread_results(t)
            # Store thread progress so we can restart at same place
            data.THREAD_DATA[i] = {"min": t.min_idx, "max": t.max_idx, "start": t.start_combo}
        print("Threads closed safely")
        raise e

    with DelayedKeyboardInterrupt():  # Ensures we don't accidentally exit the code while updating crucial data
        data.HISTORY["last_batch_size"] = data.HISTORY["batch_size"]
        data.HISTORY["batch_size"] = len(data.HISTORY["elements"])
        data.HISTORY["level"] += 1

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
        start = time.time_ns()
        evolve(num_threads=10, sleep=0.5)
        duration = (time.time_ns() - start) / 1000000000
        print(f"LEVEL {data.HISTORY['level'] - 1}: Duration - {duration} s; "
              f"Found {data.HISTORY['batch_size'] - data.HISTORY['last_batch_size']} new crafts")
        print("---------------")
        data.dump()

    finally:
        # for s in SESSIONS:
        #    s.close()
        SESSION.close()
        data.dump()
        print("Data saved")
