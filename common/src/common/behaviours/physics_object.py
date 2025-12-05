from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pygame as pg

from common.behaviour import Behaviour
from common.behaviours.collider import Collider, shape_collides
from common.primitives import Vector2


@dataclass
class Collision:
    this_physics_object: PhysicsObject
    this_collider: Collider
    other_collider: Collider
    other_physics_object: PhysicsObject | None

    def inverted(self):
        assert self.other_physics_object is not None
        return Collision(
            this_physics_object=self.other_physics_object,
            this_collider=self.other_collider,
            other_collider=self.this_collider,
            other_physics_object=self.this_physics_object,
        )


class CollisionHandler:
    def on_collision_enter(self, collision: Collision) -> Any:
        pass

    def on_collision_exit(
        self, collider: Collider, physics_object: PhysicsObject | None
    ) -> Any:
        pass


class PhysicsObject(Behaviour):
    def on_init(self) -> Any:
        self.mass: float = 1
        self._pending_motion = Vector2()
        self._contacts: set[Collider] = set()

    def on_pre_start(self):
        self.collider = self.node.get_or_add_behaviour(Collider)

    @property
    def world(self):
        return self.collider.world

    def move_and_collide(self, motion: Vector2):
        self._pending_motion += motion

    def on_tick(self, tick_id: int):
        if self._pending_motion.length_squared() == 0:
            return

        self._perform_motion(self._pending_motion)
        self._pending_motion = Vector2(0, 0)

    def _perform_motion(self, motion: Vector2):
        SQ_TOL = 0.1 * 0.1
        world = self.world
        if world is None:
            return

        old_rect = self.collider.get_bounding_rect()
        sq_error = motion.length_squared()

        new_pos = old_rect.center + motion
        new_rect = self.collider.get_bounding_rect(motion)

        new_contacts: set[Collider] = set()
        collision: Collision | None = None

        for other in world.get_potential_contacts(new_rect):
            if other is self.collider:
                continue

            other_rect = other.get_bounding_rect()
            other_pos = other_rect.center

            collides = shape_collides(
                (new_pos, self.collider.scaled_shape),
                (other_pos, other.scaled_shape),
            )

            if not collides:
                continue

            new_contacts.add(other)

            lb, ub = 0.0, 1.0
            mid = 0.5

            while sq_error > SQ_TOL:
                if collides:
                    ub = mid
                else:
                    lb = mid

                sq_error /= 4
                new_pos = old_rect.center + motion * mid

                collides = shape_collides(
                    (new_pos, self.collider.scaled_shape),
                    (other_pos, other.scaled_shape),
                )

                mid = (lb + ub) * 0.5

            other_po = other.node.get_behaviour(PhysicsObject)
            collision = Collision(
                this_physics_object=self,
                this_collider=self.collider,
                other_collider=other,
                other_physics_object=other_po,
            )

            if other not in self._contacts:
                self._fire_collision_enter(collision)
                if other_po:
                    other_po._fire_collision_enter(collision.inverted())

            if other_po is not None:
                remaining_motion = motion - motion * mid
                push = remaining_motion * (self.mass / other_po.mass)
                other_po.move_and_collide(push)

        self.transform.position = new_pos

        for prev in self._contacts:
            if prev not in new_contacts:
                po = prev.node.get_behaviour(PhysicsObject)
                self._fire_collision_exit(prev, po)
                if po:
                    po._fire_collision_exit(prev, self)

        self._contacts = new_contacts

    def _fire_collision_enter(self, collision: Collision):
        assert self.game
        for b in self.node.behaviours:
            if isinstance(b, CollisionHandler):
                self.game.simulation.run_task(b.on_collision_enter(collision))

    def _fire_collision_exit(
        self, collider: Collider, physics_object: PhysicsObject | None
    ):
        assert self.game
        for b in self.node.behaviours:
            if isinstance(b, CollisionHandler):
                self.game.simulation.run_task(
                    b.on_collision_exit(collider, physics_object)
                )
