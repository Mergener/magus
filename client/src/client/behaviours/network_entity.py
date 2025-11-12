from typing import Callable

from client.behaviours.animator import Animator
from client.behaviours.entities import NETWORK_ENTITIES_SETUP
from client.behaviours.mage import Mage
from client.behaviours.sprite_renderer import SpriteRenderer
from common.engine.behaviour import Behaviour
from common.engine.node import Node
from common.magus.entity_type import EntityType


class NetworkEntity(Behaviour):
    def on_init(self):
        self._id: int = 0

    def setup(self, type: EntityType):
        NETWORK_ENTITIES_SETUP.get(type, lambda node: node)(self.node)
