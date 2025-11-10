from __future__ import annotations

from collections import defaultdict

import pygame as pg

from common.behaviour import Behaviour
from common.utils import overrides_method


class Simulation:
    def __init__(self, tick_rate: float = 1 / 15):
        self.tick_rate = tick_rate
        self._last_tick: float = 0
        self._tick_accum_time: float = 0
        self._tick_id = 0
        self._updatables: set[Behaviour] = set()
        self._tickables: set[Behaviour] = set()
        self._renderables: defaultdict[int, set[Behaviour]] = defaultdict(set)

    @property
    def tick_id(self):
        return self._tick_id

    def add_updatable(self, b: Behaviour):
        if overrides_method(Behaviour, b, "on_update"):
            self._updatables.add(b)

    def add_tickable(self, b: Behaviour):
        if overrides_method(Behaviour, b, "on_tick"):
            self._tickables.add(b)

    def add_renderable(self, b: Behaviour, layer: int):
        if overrides_method(Behaviour, b, "on_render"):
            self._renderables[layer].add(b)

    def remove_updatable(self, b: Behaviour):
        self._updatables.discard(b)

    def remove_tickable(self, b: Behaviour):
        self._tickables.discard(b)

    def remove_renderable(self, b: Behaviour, layer: int):
        self._renderables[layer].discard(b)

    def start(self):
        self._last_tick = pg.time.get_ticks()

    def iterate(self):
        curr_tick = pg.time.get_ticks()
        dt = (curr_tick - self._last_tick) / 1000.0
        self._last_tick = curr_tick
        self._tick_accum_time += dt

        if self._tick_accum_time > self.tick_rate:
            self._tick_accum_time -= self.tick_rate
            for t in self._tickables:
                t.on_tick(self._tick_id)
            self._tick_id += 1

        for u in self._updatables:
            u.on_update(dt)

    def render(self):
        for l in sorted(self._renderables.keys()):
            for r in self._renderables[l]:
                r.on_render()
