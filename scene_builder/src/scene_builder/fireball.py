import pygame as pg

from common.animation import Animation, AnimationFrame, SliceMode, slice_image
from common.assets import load_image_asset, load_node_asset
from common.behaviours.animator import Animator
from common.behaviours.sprite_renderer import SpriteRenderer
from common.node import Node
from game.spells.fireball_projectile import FireballProjectile
from scene_builder.base import save_animation, save_node


def build_fireball_projectile():
    projectile = Node()

    projectile.add_behaviour(FireballProjectile)

    spritesheet = load_image_asset("img/spells/fireball.png")
    sprites = slice_image(spritesheet, pg.Vector2(4, 10), SliceMode.RECTS_PER_AXIS)
    frames = [AnimationFrame(s) for s in sprites]

    # Animations
    spawn = Animation(frames[0:12], 25, "animations/fireball/spawn.json")
    idle = Animation(frames[12:24], 25, "animations/fireball/idle.json")
    burst = Animation(frames[28:], 20, "animations/fireball/burst.json")

    animator = projectile.add_behaviour(Animator)
    animator.animations = {
        "spawn": spawn,
        "idle": idle,
        "burst": burst,
    }
    for anim in animator.animations.values():
        save_animation(anim)

    sprite_renderer = projectile.get_or_add_behaviour(SpriteRenderer)
    sprite_renderer.image_scale = pg.Vector2(0.3, 0.3)

    save_node(projectile, "templates/spells/fireball_projectile.json")
