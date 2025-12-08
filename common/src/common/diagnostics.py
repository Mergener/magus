import time
from collections import defaultdict
from contextlib import contextmanager
from re import T


class Profiler:
    def __init__(self):
        self._current: defaultdict[str, float] = defaultdict(float)
        self._last: defaultdict[str, float] = defaultdict(float)
        self._stacks: defaultdict[str, list[float]] = defaultdict(list)

    def step(self):
        self._last = self._current
        self._current = defaultdict(float)

    def get_last(self, topic: str):
        return self._last.get(topic, 0)

    def profile_begin(self, topic: str):
        self._stacks[topic].append(time.perf_counter())

    def profile_end(self, topic: str):
        try:
            end = time.perf_counter()
            begin = self._stacks[topic].pop()
            delta = end - begin
            self._current[topic] += delta
            return delta
        except:
            return 0

    @property
    def topics(self):
        return self._last.keys()

    @contextmanager
    def profile(self, topic: str):
        self.profile_begin(topic)
        try:
            yield
        finally:
            self.profile_end(topic)
