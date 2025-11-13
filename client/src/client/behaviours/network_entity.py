from typing import Callable

from client.behaviours.entities import NETWORK_ENTITIES_ASSETS
from client.behaviours.mage import Mage
from client.behaviours.sprite_renderer import SpriteRenderer
from common.engine.animator import Animator
from common.engine.behaviour import Behaviour
from common.engine.node import Node
from common.magus.entity_type import EntityType


class NetworkEntity(Behaviour):
    def on_init(self):
        self._id: int = 0
