from __future__ import annotations

import pygame as pg

from abc import ABC
from typing import cast, Self
from common.utils import overrides_method


class Simulation:
    def __init__(self, tick_rate: float = 1 / 15):
        self.tick_rate = tick_rate
        self._tick_accum_time = 0
        self._tick_id = 0
        self._updatables: set[Behaviour] = set()
        self._tickables: set[Behaviour] = set()
        self._renderables: set[Behaviour] = set()

    @property
    def tick_id(self):
        return self._tick_id

    def add_updatable(self, b: Behaviour):
        if overrides_method(Behaviour, b, "on_update"):
            self._updatables.add(b)

    def add_tickable(self, b: Behaviour):
        if overrides_method(Behaviour, b, "on_tick"):
            self._tickables.add(b)

    def add_renderable(self, b: Behaviour):
        if overrides_method(Behaviour, b, "on_render"):
            self._renderables.add(b)

    def remove_updatable(self, b: Behaviour):
        self._updatables.discard(b)

    def remove_tickable(self, b: Behaviour):
        self._tickables.discard(b)

    def remove_renderable(self, b: Behaviour):
        self._renderables.discard(b)

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
        for r in self._renderables:
            r.on_render()


class Node:
    def __init__(self, behaviours: list[Behaviour] = []):
        self._children: list[Self] = []
        self._simulation: Simulation | None = None
        self._parent: Self | None = None

        self._behaviours: list[Behaviour] = []
        self.add_behaviour(Transform())
        for b in behaviours:
            self.add_behaviour(b)

    @property
    def parent(self):
        return self._parent

    def get_behaviour[T: Behaviour](self, t: type[T]) -> T | None:
        for b in self._behaviours:
            if isinstance(b, t):
                return b
        return None

    def add_behaviour(self, b: Behaviour):
        if b in self._behaviours:
            return

        b._set_node(self)

        self._behaviours.append(b)

    @property
    def transform(self) -> "Transform":
        return cast("Transform", self._behaviours[0])

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
                    self._simulation.add_renderable(b)

        self._simulation = simulation

        if simulation is not None:
            for b in self._behaviours:
                if b.receive_updates:
                    self._simulation.add_updatable(b)
                    self._simulation.add_tickable(b)

                if b.visible:
                    self._simulation.add_renderable(b)


class Behaviour(ABC):
    def __init__(self):
        self._node: Node | None = None
        self._receive_updates: bool = True
        self._visible: bool = True
        self._render_layer: int = 0

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
        if self._node == node:
            return

        if self.node != None and self.simulation:
            self.simulation.remove_renderable(self)
            self.simulation.remove_tickable(self)
            self.simulation.remove_updatable(self)

        self._node = node

        # Setting properties so that setters are invoked.
        self.visible = self.visible
        self.receive_updates = self.receive_updates

        self.on_start()

    @property
    def simulation(self) -> Simulation | None:
        return self._node.simulation if self._node is not None else None

    @property
    def parent(self):
        return self._node.parent if self._node else None

    @property
    def transform(self):
        return self._node.transform if self._node else None

    @property
    def receive_updates(self):
        return self._receive_updates

    @receive_updates.setter
    def receive_updates(self, rcv: bool):
        self._receive_updates = rcv
        if self.simulation == None:
            return

        if rcv:
            self.simulation.add_tickable(self)
            self.simulation.add_updatable(self)
        else:
            self.simulation.remove_updatable(self)
            self.simulation.remove_tickable(self)

    @property
    def render_layer(self):
        return self._render_layer

    @render_layer.setter
    def render_layer(self, layer: int):
        self.render_layer = layer

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, vis: bool):
        self._visible = vis
        if self.simulation == None:
            return

        if vis:
            self.simulation.add_renderable(self)
        else:
            self.simulation.remove_renderable(self)


class Transform(Behaviour):
    def __init__(self):
        super().__init__()
        self._local_position = pg.Vector2(0, 0)
        self._local_scale = pg.Vector2(1, 1)
        self._rotation = 0

    @property
    def local_scale(self):
        return self._local_scale

    @property
    def scale(self) -> pg.Vector2:
        scale = self._local_scale
        if self.parent != None:
            scale = pg.Vector2(self.parent.transform.scale.x * scale.x, self.parent.transform.scale.y * scale.y)
        return scale

    @property
    def local_position(self):
        return self.local_position

    @local_position.setter
    def local_position(self, new_pos: pg.Vector2):
        self.local_position = new_pos

    @property
    def position(self) -> pg.Vector2:
        position = self._local_position
        if self.parent != None:
            position += self.parent.transform.position
        return position

    @position.setter
    def position(self, new_pos: pg.Vector2):        
        delta = new_pos - self.position
        self.local_position += delta
