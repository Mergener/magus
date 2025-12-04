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
    def on_init(self) -> Any:
        self.mass: float = 1

    def on_pre_start(self):
        self.collider = self.node.get_or_add_behaviour(Collider)

    @property
    def world(self):
        return self.collider.world

    def move_and_collide(self, motion: pg.Vector2) -> Collision | None:
        SQ_TOL = 0.1 * 0.1

        world = self.world
        if world is None:
            return None

        sq_error = motion.length_squared()

        old_rect = self.collider.get_bounding_rect()
        new_rect = self.collider.get_bounding_rect(motion)
        new_world_pos = old_rect.center + motion
        collision: Collision | None = None

        for c in world.get_potential_contacts(new_rect):
            if c is self.collider:
                continue

            c_rect = c.get_bounding_rect()
            c_pos = c_rect.center

            collides = shape_collides(
                (new_world_pos, self.collider.scaled_shape), (c_pos, c.scaled_shape)
            )
            if not collides:
                continue

            lb = 0
            ub = 1
            middle = (lb + ub) / 2
            while sq_error > SQ_TOL:
                if collides:
                    ub = middle
                else:
                    lb = middle
                sq_error /= 4

                new_world_pos = old_rect.center + motion * middle
                collides = shape_collides(
                    (new_world_pos, self.collider.scaled_shape), (c_pos, c.scaled_shape)
                )
                middle = (lb + ub) / 2

            collision = Collision(
                this_physics_object=self,
                this_collider=self.collider,
                other_collider=c,
                other_physics_object=c.node.get_behaviour(PhysicsObject),
            )

            other_po = collision.other_physics_object
            if other_po is not None:
                mass_ratio = self.mass / other_po.mass
                other_po.move_and_collide((motion - (middle * motion)) * mass_ratio)

        self.transform.position = new_world_pos
        return collision

    def on_serialize(self, out_dict: dict):
        out_dict["mass"] = self.mass

    def on_deserialize(self, in_dict: dict):
        self.mass = in_dict.get("mass", 1)
