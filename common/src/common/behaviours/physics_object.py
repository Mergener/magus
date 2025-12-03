from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pygame as pg

from common.behaviour import Behaviour
from common.behaviours.collider import Collider

if TYPE_CHECKING:
    from common.behaviours.physics_world import Collision


class PhysicsObject(Behaviour):
    def on_pre_start(self) -> Any:
        from common.behaviours.physics_world import PhysicsWorld

        assert self.game
        world = self.game.scene.get_behaviour_in_children(PhysicsWorld)

        self.collider = self.node.get_behaviour(Collider)
