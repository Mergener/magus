from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from typing import Any

import pygame as pg

from common.behaviour import Behaviour
from common.game import Profiler
from common.utils import overrides_method


class Simulation:
    def __init__(self, profiler: Profiler | None, tick_rate: float = 24):
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
        self._frame_futures: list[asyncio.Future] = []
        self._tick_futures: list[asyncio.Future] = []
        self._pending_tasks: set[asyncio.Task] = set()
        self._profiler = profiler or Profiler()

        self.render_debug = False

    def _spawn_task(self, coro):
        task = asyncio.create_task(coro)
        self._pending_tasks.add(task)

        def _cleanup(task):
            self._pending_tasks.discard(task)
            try:
                task.result()
            except Exception as e:
                print("Async task error:", e)

        task.add_done_callback(_cleanup)

    def run_task(self, value: Any):
        if asyncio.iscoroutine(value):
            self._spawn_task(value)
        return value

    @property
    def tick_id(self):
        return self._tick_id

    @property
    def tick_rate(self):
        return 1 / self.tick_interval

    @tick_rate.setter
    def tick_rate(self, tick_rate: float):
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
        from common.behaviours.ui.widget import Widget

        if isinstance(b, Widget):
            layer += 10000

        if overrides_method(Behaviour, b, "on_render") or overrides_method(
            Behaviour, b, "on_debug_render"
        ):
            self._will_render.add((b, layer))

    def remove_updatable(self, b: Behaviour):
        self._will_stop_updating.add(b)
        self._will_update.discard(b)

    def remove_renderable(self, b: Behaviour, layer: int):
        from common.behaviours.ui.widget import Widget

        if isinstance(b, Widget):
            layer += 10000

        self._will_stop_rendering.add((b, layer))
        self._will_render.discard((b, layer))

    def start(self):
        self._last_tick = pg.time.get_ticks()

    def iterate(self):
        curr_tick = pg.time.get_ticks()
        dt = (curr_tick - self._last_tick) / 1000.0
        self.last_frame_time = dt
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
            if ts._started or ts.node.destroyed:
                continue
            self.run_task(ts.on_pre_start())

        for ts in starting:
            if ts._started or ts.node.destroyed:
                continue
            ts._started = True
            self.run_task(ts.on_start())

        self._resolve_frame_futures()

        with self._profiler.profile("tick"):
            if self._tick_accum_time > self.tick_interval:
                self._tick_accum_time -= self.tick_interval
                self._resolve_tick_futures()
                for t in self._tickables:
                    if t.node.destroyed:
                        continue
                    self.run_task(t.on_tick(self._tick_id))
                self._tick_id += 1

        with self._profiler.profile("update"):
            for u in self._updatables:
                if u.node.destroyed:
                    continue
                self.run_task(u.on_update(dt))

    def render(self):
        for bl in self._will_render:
            behaviour, layer = bl
            self._renderables[layer].add(behaviour)

        for bl in self._will_stop_rendering:
            behaviour, layer = bl
            self._renderables[layer].discard(behaviour)

        self._will_stop_rendering.clear()
        self._will_render.clear()

        sorted_render_layers = self._renderables.keys()
        for l in sorted(sorted_render_layers):
            for r in self._renderables[l]:
                if r.node.destroyed:
                    continue
                r.on_render()

            if self.render_debug:
                for r in self._renderables[l]:
                    if r.node.destroyed:
                        continue
                    r.on_debug_render()

    async def wait_next_frame(self):
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        self._frame_futures.append(future)
        return await future

    async def wait_next_tick(self):
        loop = asyncio.get_event_loop()
        future = loop.create_future()
        self._tick_futures.append(future)
        return await future

    async def wait_seconds(self, seconds: float):
        start_time = pg.time.get_ticks() / 1000.0
        target_time = start_time + seconds

        while True:
            current_time = pg.time.get_ticks() / 1000.0
            if current_time >= target_time:
                break
            await self.wait_next_frame()

    def _resolve_frame_futures(self):
        futures_to_resolve = self._frame_futures.copy()
        self._frame_futures.clear()

        for future in futures_to_resolve:
            if not future.done():
                future.set_result(None)

    def _resolve_tick_futures(self):
        futures_to_resolve = self._tick_futures.copy()
        self._tick_futures.clear()

        for future in futures_to_resolve:
            if not future.done():
                future.set_result(None)
