import json
from typing import TYPE_CHECKING, Callable

import pygame as pg

from client.behaviours.mage import Mage
from client.behaviours.sprite_renderer import SpriteRenderer
from common.engine.animator import Animator
from common.engine.assets import load_image_asset
from common.engine.behaviour import Behaviour
from common.engine.node import Node
from common.magus.entity_type import EntityType

if TYPE_CHECKING:
    from common.engine.animation import Animation


def setup_mage(node: Node):
    from common.engine.animation import (
        Animation,
        AnimationFrame,
        SliceMode,
        slice_image,
    )

    node.add_behaviour(SpriteRenderer)
    animator = node.add_behaviour(Animator)

    mage_sheet = load_image_asset("img/mage.png")
    quads = slice_image(mage_sheet, pg.Vector2(8, 4), SliceMode.RECTS_PER_AXIS)
    animation_frames = [AnimationFrame(q) for q in quads]
    mage_animation = Animation(animation_frames, 10)
    animator.animation = mage_animation

    mage = node.add_behaviour(Mage)


NETWORK_ENTITIES_SETUP: dict[EntityType, Callable[[Node], None]] = {
    EntityType.MAGE: setup_mage
}
