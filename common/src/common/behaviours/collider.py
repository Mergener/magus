from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import pygame as pg

from common.behaviour import Behaviour
from common.behaviours.physics_world import PhysicsWorld


@dataclass
class Collision:
    pass


class Collider(Behaviour, ABC):
    def on_pre_start(self) -> Any:
        assert self.game
        self._world = self.game.scene.get_behaviour_in_children(PhysicsWorld)


class RectCollider(Collider):
    def on_init(self) -> Any:
        self.size = pg.Vector2(100, 100)
        self.offset = pg.Vector2(0, 0)

    @property
    def rect(self):
        return pg.Rect(
            self.transform.position + self.offset - (self.size / 2), self.size
        )
