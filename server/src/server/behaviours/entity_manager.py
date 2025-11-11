from common.engine.behaviour import Behaviour
from common.engine.node import Node


class EntityManager(Behaviour):
    _entities: dict[int, Node]

    def on_init(self):
        self._entities = {}
