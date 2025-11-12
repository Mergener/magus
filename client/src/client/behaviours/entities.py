from typing import Callable

import pygame as pg

from client.animation import Animation, AnimationFrame, SliceMode, slice_image
from client.behaviours.animator import Animator
from client.behaviours.mage import Mage
from client.behaviours.sprite_renderer import SpriteRenderer
from common.engine.assets import load_image_asset
from common.engine.behaviour import Behaviour
from common.engine.node import Node
from common.magus.entity_type import EntityType

_mage_animation: Animation | None = None


def setup_mage(node: Node):
    global _mage_animation

    renderer = node.add_behaviour(SpriteRenderer)
    animator = node.add_behaviour(Animator)
    if _mage_animation is None:
        mage_sheet = load_image_asset("img/mage.png")
        quads = slice_image(mage_sheet, pg.Vector2(8, 4), SliceMode.RECTS_PER_AXIS)
        animation_frames = [AnimationFrame(q) for q in quads]
        _mage_animation = Animation(animation_frames, 10)
        animator.animation = _mage_animation

    mage = node.add_behaviour(Mage)


NETWORK_ENTITIES_SETUP: dict[EntityType, Callable[[Node], None]] = {
    EntityType.MAGE: setup_mage
}
