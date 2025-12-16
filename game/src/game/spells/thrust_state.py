import pygame as pg

from common.primitives import Vector2
from game.spell import SpellState


class ThrustState(SpellState):
    def on_point_cast(self, target: Vector2):
        self._mage.physics_object.knock_back(
            (target - self._mage.transform.position).normalize()
            * (
                self.get_current_level_data("force", 0.0)
                * self._mage.mass.current
                / 100
            )
        )
