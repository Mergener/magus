import json
from typing import TYPE_CHECKING, Callable

import pygame as pg

from client.behaviours.mage import Mage
from client.behaviours.sprite_renderer import SpriteRenderer
from common.engine.animator import Animator
from common.engine.assets import load_image_asset, load_node_asset
from common.engine.behaviour import Behaviour
from common.engine.node import Node
from common.magus.entity_type import EntityType

if TYPE_CHECKING:
    from common.engine.animation import Animation


NETWORK_ENTITIES_ASSETS: dict[EntityType, str] = {EntityType.MAGE: "objects/mage.json"}
