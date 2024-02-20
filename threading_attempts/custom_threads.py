import threading
import requests
import time
import json
from json.decoder import JSONDecodeError
from data import NULL_RECIPE_KEY

class IPBlockException(RuntimeError):
    def __init__(self, retry_time: int):
        super().__init__(f"Infinite Craft has temporarily IP-blocked this session. "
                         f"Can retry in {retry_time} seconds.", )
        self.retry_time = retry_time

class CrafterThread(threading.Thread):
    def __init__(self, session: requests.Session, history: dict[str, any], start_combo: tuple[int, int],
                 min_idx: int, max_idx: int, sleep=0.0):
        """
        Creates a CrafterThread object, and automatically generates the combinations it
        will try from the given points.

        :param session: the session used by the thread
        :param history: the history object to use for datakeeping
        :param start_combo: the combination to start with. Also determines lower,
        inclusive limit for the first combinee
        :param min_idx: the lower, inclusive limit for the second combinee
        :param max_idx: the upper, exclusive limit for the combinees
        :param sleep: the time between trying combinations
        """
        super().__init__(target=self.process)
        self.session = session
        self.history = history
        self.start_combo = start_combo
        self.min_idx = min_idx
        self.max_idx = max_idx
        self.sleep = sleep
        self.batch: list[tuple[int, int]] = []
        self.crafted: list[str] = []
        self.recipes: dict[str, list[str]] = {NULL_RECIPE_KEY: []}
        self.levels: dict[str, int] = {}
        self.new_recipes: list[str] = []
        self.cancel = False
        self.exception: Exception | None = None
        self.success = False

        # Process batch
        for j in range(start_combo[1], max_idx):
            self.batch.append((start_combo[0], j))  # Only check ones that came after our last combo

        for i in range(start_combo[0] + 1, max_idx):
            for j in range(max(i, min_idx), max_idx):
                self.batch.append((i, j))  # Only check ones that came after our last combo

    def combine(self, one: str, two: str):
        """
        Constructs a HTTP GET request emulating combining the two elements,
        sends it to neal.fun, and returns the result.
        """
        params = {
            'first': one,
            'second': two,
        }

        response = self.session.get('https://neal.fun/api/infinite-craft/pair', params=params)
        try:
            return json.loads(response.content.decode('utf-8'))
        except JSONDecodeError:
            if "Retry-After" in response.headers:
                raise IPBlockException(int(response.headers["Retry-After"])) from None

    def kill(self):
        self.cancel = True

    def join(self, timeout: float | None = None, ignore_exceptions=False) -> None:
        super().join(timeout)
        if not ignore_exceptions and self.exception is not None:
            raise self.exception

    def process(self):
        """The function that runs during the thread. Automatically stops if self.cancel is true."""
        try:
            for i, combo in enumerate(self.batch):
                if self.cancel:
                    self.success = False
                    return

                e1 = self.history["elements"][combo[0]]
                e2 = self.history["elements"][combo[1]]
                recipe_key = e1 + ";" + e2

                result_json = self.combine(e1, e2)
                result_key = result_json["result"]

                if result_key == "Nothing":
                    self.recipes[NULL_RECIPE_KEY].append(recipe_key)
                    print(f"NULL RECIPE: {e1} + {e2}")
                    continue

                print(f"{e1} + {e2} = {result_key}")

                # Update recipes
                if result_key not in self.recipes:
                    self.recipes[result_key] = [recipe_key]
                elif recipe_key not in self.recipes[result_key]:
                    self.recipes[result_key].append(recipe_key)

                # Update our history
                if result_key not in self.crafted:
                    self.crafted.append(result_key)

                if result_key not in self.levels:
                    self.levels[result_key] = self.history["level"]

                # Keep track of new discoveries
                if result_json["isNew"]:
                    print(f"NEW DISCOVERY: {e1} + {e2} = {result_key}")
                    self.new_recipes.append(result_key)

                self.start_combo = combo  # Update start combo
                time.sleep(self.sleep)

            # we only get here if we complete everything
            self.success = True
        except Exception as e:
            self.exception = e
