from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pygame as pg

from common.behaviour import Behaviour
from common.behaviours.collider import Collider, shape_collides

if TYPE_CHECKING:
    from common.behaviours.physics_object import PhysicsObject


@dataclass
class Collision:
    this_physics_object: "PhysicsObject"
    this_collider: Collider
    other_collider: Collider
    other_physics_object: "PhysicsObject | None"


class PhysicsObject(Behaviour):
    def on_pre_start(self):
        self.collider = self.node.get_or_add_behaviour(Collider)

    @property
    def world(self):
        return self.collider.world

    def move_and_collide(self, motion: pg.Vector2):
        new_pos = self.transform.local_position + motion
        new_rect = self.collider.get_bounding_rect(new_pos)

        for c in self.world.get_potential_contacts(new_rect):
            if c is self.collider:
                continue

            c_rect = c.get_bounding_rect()
            c_pos = pg.Vector2(c_rect.x, c_rect.y)

            if not shape_collides((new_pos, self.collider.shape), (c_pos, c.shape)):
                continue

            return Collision(
                self,
                self.collider,
                c,
                c.node.get_behaviour(PhysicsObject),
            )

        self.transform.local_position = new_pos
        return None
