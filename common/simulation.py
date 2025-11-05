from __future__ import annotations

from abc import ABC
from collections import defaultdict
from typing import Self, cast

import pygame as pg

from common.utils import memberwise_multiply, overrides_method


class Simulation:
    def __init__(self, tick_rate: float = 1 / 15):
        self.tick_rate = tick_rate
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

    def update(self, dt):
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


class Node:
    def __init__(self):
        self._children: list[Self] = []
        self._simulation: Simulation | None = None
        self._parent: Self | None = None

        self._behaviours: list[Behaviour] = []
        self.add_behaviour(Transform)

    @property
    def parent(self):
        return self._parent

    def get_behaviour[T: Behaviour](self, t: type[T]) -> T | None:
        for b in self._behaviours:
            if isinstance(b, t):
                return b
        return None

    def add_behaviour[T: Behaviour](self, tb: type[T]) -> T:
        b = tb(self)
        self._behaviours.append(b)
        return b

    @property
    def transform(self) -> Transform:
        return cast(Transform, self._behaviours[0])

    @property
    def simulation(self) -> Simulation | None:
        return self._simulation

    @simulation.setter
    def simulation(self, simulation: Simulation):
        if self._simulation is not None:
            for b in self._behaviours:
                if b.receive_updates:
                    self._simulation.add_updatable(b)
                    self._simulation.add_tickable(b)

                if b.visible:
                    self._simulation.add_renderable(b, b.render_layer)

        self._simulation = simulation

        if simulation is not None:
            for b in self._behaviours:
                if b.receive_updates:
                    self._simulation.add_updatable(b)
                    self._simulation.add_tickable(b)

                if b.visible:
                    self._simulation.add_renderable(b, b.render_layer)


class Behaviour(ABC):
    def __init__(self, node: Node):
        self._receive_updates: bool = True
        self._visible: bool = True
        self._render_layer: int = 0
        self._set_node(node)
        self.on_init()

    def on_init(self):
        pass

    def on_start(self):
        pass

    def on_update(self, dt: float):
        pass

    def on_tick(self, tick_id: int):
        pass

    def on_destroy(self):
        pass

    def on_render(self):
        pass

    @property
    def node(self):
        return self._node

    def _set_node(self, node: Node):
        if hasattr(self, "_node") and self.node != None and self.node._simulation:
            self.node._simulation.remove_renderable(self, self.render_layer)
            self.node._simulation.remove_tickable(self)
            self.node._simulation.remove_updatable(self)

        self._node = node

        # Setting properties so that setters are invoked.
        self.visible = self.visible
        self.receive_updates = self.receive_updates

        self.on_start()

    @property
    def parent(self):
        return self._node.parent

    @property
    def transform(self):
        return self._node.transform

    @property
    def receive_updates(self):
        return self._receive_updates

    @receive_updates.setter
    def receive_updates(self, rcv: bool):
        self._receive_updates = rcv
        if self.node._simulation is None:
            return

        if rcv:
            self.node._simulation.add_tickable(self)
            self.node._simulation.add_updatable(self)
        else:
            self.node._simulation.remove_updatable(self)
            self.node._simulation.remove_tickable(self)

    @property
    def render_layer(self):
        return self._render_layer

    @render_layer.setter
    def render_layer(self, layer: int):
        if self.node.simulation is not None:
            self.node.simulation.remove_renderable(self, self._render_layer)
            self.node.simulation.add_renderable(self, layer)
        self._render_layer = layer

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, vis: bool):
        self._visible = vis
        if self.node.simulation is None:
            return

        if vis:
            self.node.simulation.add_renderable(self, self._render_layer)
        else:
            self.node.simulation.remove_renderable(self, self._render_layer)


class Transform(Behaviour):
    def __init__(self, node: Node):
        super().__init__(node)
        self._local_position = pg.Vector2(0, 0)
        self._local_scale = pg.Vector2(1, 1)
        self._rotation = 0

    @property
    def local_scale(self):
        return self._local_scale

    @local_scale.setter
    def local_scale(self, value: pg.Vector2):
        self._local_scale = value

    @property
    def scale(self):
        scale = self._local_scale
        if self.parent != None:
            scale = memberwise_multiply(self.local_scale, self.parent.transform.scale)
        return scale

    @property
    def local_position(self):
        return self._local_position

    @local_position.setter
    def local_position(self, new_pos: pg.Vector2):
        self._local_position = new_pos

    @property
    def position(self):
        position = self._local_position
        if self.parent is not None:
            position += self.parent.transform.position
        return position

    @position.setter
    def position(self, new_pos: pg.Vector2):
        delta = new_pos - self.position
        self.local_position += delta
