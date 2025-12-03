from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pygame as pg

from common.behaviour import Behaviour
from common.behaviours.collider import Collider


@dataclass
class Collision:
    this_physics_object: PhysicsObject
    this_collider: Collider
    other_collider: Collider
    other_physics_object: PhysicsObject | None


class PhysicsObject(Behaviour):
    def on_pre_start(self) -> Any:
        from common.behaviours.physics_world import PhysicsWorld

        assert self.game
        world = self.game.scene.get_behaviour_in_children(PhysicsWorld)

        self.collider = self.node.get_or_add_behaviour(Collider)

    def move_and_collide(self):
        pass
