"""Safety watchdog timer to ensure continuous heartbeat."""
import threading
import time
from typing import Callable, Optional


class Watchdog:
    """Watchdog timer that triggers a callback if not kicked within timeout."""

    def __init__(self, timeout_sec: float = 1.0, on_timeout: Optional[Callable] = None):
        self.timeout_sec = timeout_sec
        self.on_timeout = on_timeout
        self._last_kick = time.time()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def kick(self):
        """Reset the watchdog timer."""
        self._last_kick = time.time()

    def start(self):
        """Start the watchdog monitoring thread."""
        self._running = True
        self._last_kick = time.time()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the watchdog monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)

    def _run(self):
        while self._running:
            time.sleep(0.05)
            if time.time() - self._last_kick > self.timeout_sec:
                if self.on_timeout:
                    self.on_timeout()
                break
