from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pygame as pg

from common.behaviour import Behaviour
from common.behaviours.collider import Collider, shape_collides

if TYPE_CHECKING:
    from common.behaviours.physics_object import PhysicsObject


@dataclass
class Collision:
    this_physics_object: PhysicsObject
    this_collider: Collider
    other_collider: Collider
    other_physics_object: PhysicsObject | None


class PhysicsObject(Behaviour):
    def on_pre_start(self):
        self.collider = self.node.get_or_add_behaviour(Collider)

    @property
    def world(self):
        return self.collider.world

    def move_and_collide(self, motion: pg.Vector2) -> Collision | None:
        world = self.world
        if world is None:
            return None

        ret: Collision | None = None

        current_world_pos = self.transform.position
        new_world_pos = current_world_pos + motion

        new_rect = self.collider.get_bounding_rect(motion)

        for c in world.get_potential_contacts(new_rect):
            if c is self.collider:
                continue

            c_rect = c.get_bounding_rect()
            c_pos = c_rect.center

            if not shape_collides(
                (new_rect.center, self.collider.scaled_shape), (c_pos, c.scaled_shape)
            ):
                continue

            ret = Collision(
                this_physics_object=self,
                this_collider=self.collider,
                other_collider=c,
                other_physics_object=c.node.get_behaviour(PhysicsObject),
            )

        self.transform.position = new_world_pos
        return ret
