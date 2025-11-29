from typing import Any

from common.behaviour import Behaviour
from common.behaviours.physics_object import PhysicsObject


class PhysicsWorld(Behaviour):
    def on_init(self) -> Any:
        self._physics_objects: set[PhysicsObject] = set()

    def on_start(self) -> Any:
        assert self.game
        for po in self.game.scene.get_behaviours_in_children(PhysicsObject):
            self._physics_objects.add(po)

    def register_physics_object(self, object: PhysicsObject):
        self._physics_objects.add(object)

    def on_tick(self, tick_id: int) -> Any:
        pass
