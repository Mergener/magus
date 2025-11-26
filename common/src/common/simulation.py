from __future__ import annotations

from collections import defaultdict

import pygame as pg

from common.behaviour import Behaviour
from common.utils import overrides_method


class Simulation:
    def __init__(self, tick_rate: float = 15):
        self.tick_rate = tick_rate
        self._last_tick: float = 0
        self._tick_accum_time: float = 0
        self._tick_id = 0

        self._updatables: set[Behaviour] = set()
        self._will_update: set[Behaviour] = set()
        self._will_stop_updating: set[Behaviour] = set()

        self._tickables: set[Behaviour] = set()
        self._will_tick: set[Behaviour] = set()
        self._will_stop_ticking: set[Behaviour] = set()

        self._renderables: defaultdict[int, set[Behaviour]] = defaultdict(set)
        self._will_render: set[tuple[Behaviour, int]] = set()
        self._will_stop_rendering: set[tuple[Behaviour, int]] = set()

        self._to_start: set[Behaviour] = set()

    @property
    def tick_id(self):
        return self._tick_id

    @property
    def tick_rate(self):
        return 1 / self.tick_interval

    @tick_rate.setter
    def tick_rate(self, tick_rate):
        self.tick_interval = 1 / tick_rate

    def add_updatable(self, b: Behaviour):
        if not b._started:
            self._to_start.add(b)
        if overrides_method(Behaviour, b, "on_update"):
            self._will_update.add(b)
            self._will_stop_updating.discard(b)
        if overrides_method(Behaviour, b, "on_tick"):
            self._will_tick.add(b)
            self._will_stop_ticking.discard(b)

    def add_renderable(self, b: Behaviour, layer: int):
        if overrides_method(Behaviour, b, "on_render"):
            self._will_render.add((b, layer))

    def remove_updatable(self, b: Behaviour):
        self._will_stop_updating.add(b)
        self._will_update.discard(b)

    def remove_renderable(self, b: Behaviour, layer: int):
        self._will_stop_rendering.add((b, layer))
        self._will_render.discard((b, layer))

    def start(self):
        self._last_tick = pg.time.get_ticks()

    def iterate(self):
        curr_tick = pg.time.get_ticks()
        dt = (curr_tick - self._last_tick) / 1000.0
        self._last_tick = curr_tick
        self._tick_accum_time += dt

        self._tickables = (self._tickables | self._will_tick) - self._will_stop_ticking
        self._updatables = (
            self._updatables | self._will_update
        ) - self._will_stop_updating
        self._will_stop_updating.clear()
        self._will_stop_ticking.clear()

        starting = self._to_start
        self._to_start = set()
        for ts in starting:
            if ts._started:
                continue
            ts.on_pre_start()

        for ts in starting:
            if ts._started:
                continue
            ts._started = True
            ts.on_start()

        if self._tick_accum_time > self.tick_interval:
            self._tick_accum_time -= self.tick_interval
            for t in self._tickables:
                t.on_tick(self._tick_id)
            self._tick_id += 1

        for u in self._updatables:
            u.on_update(dt)

    def render(self):
        for bl in self._will_render:
            behaviour, layer = bl
            self._renderables[layer].add(behaviour)

        for bl in self._will_stop_rendering:
            behaviour, layer = bl
            self._renderables[layer].discard(behaviour)

        self._will_stop_rendering.clear()
        self._will_render.clear()

        for l in sorted(self._renderables.keys()):
            for r in self._renderables[l]:
                r.on_render()
