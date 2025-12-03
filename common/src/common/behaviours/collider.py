from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Any

import pygame as pg

from common.behaviour import Behaviour
from common.behaviours.physics_world import PhysicsWorld


@dataclass
class CircleCollisionShape:
    radius: float


@dataclass
class RectCollisionShape:
    size: pg.Vector2


CollisionShape = RectCollisionShape | CircleCollisionShape


class Collider(Behaviour):
    _shape: CollisionShape
    _bounding_rect: pg.Rect | None
    _last_position: pg.Vector2

    def on_init(self) -> Any:
        self._offset = pg.Vector2(0, 0)
        self._last_position = self.transform.position
        self._prev_bouding_rect = self.get_bounding_rect()
        self._cached_world: PhysicsWorld | None = None

        self.shape = RectCollisionShape(pg.Vector2(100, 100))

    def on_pre_start(self) -> Any:
        from common.behaviours.physics_world import PhysicsWorld

        assert self.game

        self._bounding_rect = None
        self.world.register_collider(self)

    @property
    def shape(self) -> CollisionShape:
        return self._shape

    @shape.setter
    def shape(self, shape: CollisionShape):
        self._shape = shape
        self._update_bounding_rect()
        self.world.update_collider_rect(self, self._bounding_rect, self._bounding_rect)

    def _update_bounding_rect(self):
        pos = pg.Vector2(self.transform.position) + self._offset

        if isinstance(self._shape, RectCollisionShape):
            size = self._shape.size
            self._bounding_rect = pg.Rect(
                int(pos.x), int(pos.y), int(size.x), int(size.y)
            )
        elif isinstance(self._shape, CircleCollisionShape):
            r = self._shape.radius
            self._bounding_rect = pg.Rect(
                int(pos.x - r),
                int(pos.y - r),
                int(r * 2),
                int(r * 2),
            )
        else:
            raise TypeError("Unknown collision shape type.")

        return self._bounding_rect

    @property
    def world(self):
        assert self.game
        world = self._cached_world
        if world is None:
            world = self.game.scene.get_behaviour_in_children(PhysicsWorld)
            if not world:
                world = self.game.scene.add_child().add_behaviour(PhysicsWorld)
            self._cached_world = world
        return world

    def get_bounding_rect(self) -> pg.Rect:
        if self._bounding_rect is None:
            return self._update_bounding_rect()
        return self._bounding_rect

    def on_tick(self, tick_id: int) -> Any:
        current_pos = self.transform.position
        if current_pos == self._last_position:
            return

        self._last_position = current_pos
        new_rect = self.get_bounding_rect()
        self.world.update_collider_rect(self, self._prev_bouding_rect, new_rect)
        self._prev_bouding_rect = new_rect
