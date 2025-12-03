import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import pygame as pg

from common.behaviour import Behaviour
from common.behaviours.collider import Collider, RectCollider
from common.behaviours.physics_object import PhysicsObject


@dataclass
class Collision:
    this_physics_object: PhysicsObject
    this_collider: Collider
    other_collider: Collider
    other_physics_object: PhysicsObject | None


# TODO: Maybe add support for other types of colliders


class PhysicsWorld(Behaviour):
    def on_init(self) -> Any:
        self._collision_grid: defaultdict[tuple[int, int], set[Collider]] = defaultdict(
            set
        )
        self.cell_w = 200
        self.cell_h = 200

    def get_potential_collisions(self, rect: pg.Rect) -> list[Collider]:
        collisions = []
        for cell in self._get_rect_grid_cells(rect):
            for c in self._collision_grid[cell]:
                collisions.append(c)
        return collisions

    def _get_rect_grid_cells(self, rect: pg.Rect):
        tlx, tly = rect.topleft
        w, h = rect.size
        for i in range(math.ceil(w / self.cell_w)):
            for j in range(math.ceil(h / self.cell_h)):
                x = tlx // self.cell_w + i
                y = tly // self.cell_h + j
                yield (x, y)

    def register_collider(self, collider: Collider):
        self.update_collider_rect(collider, None, collider.get_bounding_rect())

    def unregister_collider(self, collider: Collider):
        self.update_collider_rect(collider, collider.get_bounding_rect(), None)

    def update_collider_rect(
        self, collider: Collider, prev_rect: pg.Rect | None, new_rect: pg.Rect | None
    ):
        if prev_rect:
            for c in self._get_rect_grid_cells(prev_rect):
                self._collision_grid[c].discard(collider)
        if new_rect:
            for c in self._get_rect_grid_cells(new_rect):
                self._collision_grid[c].add(collider)
