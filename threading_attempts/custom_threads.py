import threading
import requests
import time
import json
from json.decoder import JSONDecodeError
from data import NULL_RECIPE_KEY
import proxy


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
class CrafterThread(threading.Thread):
    def __init__(self, history: dict[str, any], start_combo: tuple[int, int],
                 min_idx: int, max_idx: int, sleep=0.0, id: int | None = None):
        """
        Creates a CrafterThread object, and automatically generates the combinations it
        will try from the given points.

        :param history: the history object to use for datakeeping
        :param start_combo: the combination to start with. Also determines lower,
        inclusive limit for the first combinee
        :param min_idx: the lower, inclusive limit for the second combinee
        :param max_idx: the upper, exclusive limit for the combinees
        :param sleep: the time between trying combinations
        :param id: the ID of the thread
        """
        super().__init__(target=self.process)
        self.session = requests.sessions.Session()
        self.session.headers = rHEADERS
        self.session.verify = False
        self.proxy = None
        self.cycle_proxy()

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
        self.ID = id

        # Process batch
        for j in range(start_combo[1], max_idx):
            self.batch.append((start_combo[0], j))  # Only check ones that came after our last combo

        for i in range(start_combo[0] + 1, max_idx):
            for j in range(max(i, min_idx), max_idx):
                self.batch.append((i, j))  # Only check ones that came after our last combo

    def cycle_proxy(self):
        self.proxy = proxy.PROXIES.popleft()
        if self.proxy is not None:
            self.session.proxies = {'https': self.proxy["parsed"]}
        proxy.PROXIES.append(self.proxy)

    def combine(self, one: str, two: str) -> dict[str, any]:
        """
        Constructs an HTTP GET request emulating combining the two elements,
        sends it to neal.fun, and returns the result.
        """
        params = {
            'first': one,
            'second': two,
        }

        try:
            response = self.session.get('https://neal.fun/api/infinite-craft/pair', params=params, timeout=10)
        except requests.exceptions.Timeout:
            # If a proxy timed out, try it with our default setup
            self.cycle_proxy()  # TODO: account for the case where there are only a few proxies
            return self.combine(one, two)  # TODO: Right now, it just recursively loops until it reaches max depth

        try:
            return json.loads(response.content.decode('utf-8'))
        except JSONDecodeError:
            self.log(f"InfiniteCraft has temporarily IP-blocked this proxy: {self.proxy} - "
                     f"Switching proxies...")
            self.cycle_proxy()  # TODO: account for the case where there are only a few proxies
            # TODO: Right now, it just recursively loops until it reaches max depth
            return self.combine(one, two)  # Retry the message with the cycled proxy

    def kill(self):
        self.cancel = True

    def join(self, timeout: float | None = None, ignore_exceptions=False) -> None:
        super().join(timeout)
        if self.session is not None:
            self.session.close()
        if not ignore_exceptions and self.exception is not None:
            raise self.exception

    def log(self, msg: str):
        print(f"[Thread #{self.ID}] {msg}")

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
                    self.log(f"NULL RECIPE: {e1} + {e2}")
                    continue

                self.log(f"{e1} + {e2} = {result_key}")

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
                    self.log(f"NEW DISCOVERY: {e1} + {e2} = {result_key}")
                    self.new_recipes.append(result_key)

                self.start_combo = combo  # Update start combo
                time.sleep(self.sleep)

            # we only get here if we complete everything
            self.success = True
        except Exception as e:
            self.exception = e
