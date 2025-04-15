class LifecycleSystem:
    def __init__(self, max_ticks=None):
        self.max_ticks = max_ticks
        self._tick = 0

    def process(self, world):
        self._tick += 1
        if self.max_ticks is not None and self._tick >= self.max_ticks:
            world.messages.emit("ExitRequested", reason="max_ticks")
