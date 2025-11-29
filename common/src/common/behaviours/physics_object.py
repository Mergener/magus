from typing import Any

import pygame as pg

from common.behaviour import Behaviour
from common.behaviours.collider import Collider


class PhysicsObject(Behaviour):
    def on_init(self) -> Any:
        self._motion = pg.Vector2()

    def on_pre_start(self) -> Any:
        from common.behaviours.physics_world import PhysicsWorld

        assert self.game
        world = self.game.scene.get_behaviour_in_children(PhysicsWorld)
        if world:
            world.register_physics_object(self)

        self.collider = self.node.get_behaviour(Collider)

    def move_and_collide(self, motion: pg.Vector2):
        self._motion += motion
