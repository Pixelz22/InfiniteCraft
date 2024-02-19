import signal
import logging


class DelayedKeyboardInterrupt:

    def __enter__(self):
        self.signal_received: bool | tuple = False
        self.old_handler = signal.signal(signal.SIGINT, self.handler)

    def handler(self, sig, frame):
        self.signal_received = (sig, frame)
        logging.debug('SIGINT received. Delaying KeyboardInterrupt.')

    def __exit__(self, type, value, traceback):
        signal.signal(signal.SIGINT, self.old_handler)
        if self.signal_received:
            self.old_handler(*self.signal_received)


def to_percent(p: float, places=2) -> float:
    return round(p * (10 ** (2 + places))) / (10 ** places)
