from common.behaviour import Behaviour
from common.node import Node


class EntityManager(Behaviour):
    _entities: dict[int, Node]

    def on_init(self):
        self._entities = {}
