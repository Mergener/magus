from __future__ import annotations

import math
from collections import defaultdict
from typing import TYPE_CHECKING, Any, cast

import pygame as pg

from common.behaviour import Behaviour
from common.primitives import Rect

if TYPE_CHECKING:
    from common.behaviours.collider import Collider


class PhysicsWorld(Behaviour):
    def on_init(self):
        self._collision_grid: defaultdict[tuple[int, int], set[Collider]] = defaultdict(
            set
        )
        self.cell_w = 200
        self.cell_h = 200

    def get_potential_contacts(self, rect: Rect):
        result: set[Collider] = set()
        for cell in self._get_rect_grid_cells(rect):
            result.update(self._collision_grid[cell])
        return list(result)

    def _get_rect_grid_cells(self, rect: Rect):
        tlx, tly = rect.topleft
        w, h = rect.size

        start_x = math.floor(tlx / self.cell_w)
        end_x = math.floor((tlx + w) / self.cell_w)
        start_y = math.floor(tly / self.cell_h)
        end_y = math.floor((tly + h) / self.cell_h)

        for x in range(start_x, end_x + 1):
            for y in range(start_y, end_y + 1):
                yield cast(tuple[int, int], (x, y))

    def register_collider(self, collider: Collider):
        self.update_collider_rect(collider, None, collider.get_bounding_rect())

    def unregister_collider(self, collider: Collider):
        self.update_collider_rect(collider, collider.get_bounding_rect(), None)

    def update_collider_rect(
        self, collider: Collider, prev_rect: Rect | None, new_rect: Rect | None
    ):
        if prev_rect:
            for c in self._get_rect_grid_cells(prev_rect):
                self._collision_grid[c].discard(collider)
        if new_rect:
            for c in self._get_rect_grid_cells(new_rect):
                self._collision_grid[c].add(collider)
