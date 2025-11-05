import traceback
from sys import stderr

import pygame as pg

from client.animation import Animation, AnimationFrame, SliceMode, slice_image
from client.assets import load_image_asset
from client.behaviours.animator import Animator
from client.behaviours.camera import Camera
from client.behaviours.player import Player
from client.behaviours.sprite_renderer import SpriteRenderer
from common import init_common
from common.simulation import Node, Simulation


def create_scene(simulation: Simulation):
    camera_node = Node()
    camera_node.simulation = simulation
    camera_node.add_behaviour(Camera)

    character = Node()
    character.transform.local_scale = pg.Vector2(4, 4)

    img = load_image_asset("img/mage.png")

    character.add_behaviour(SpriteRenderer).tint = pg.Color(0, 0, 255, 128)
    quads = slice_image(img, pg.Vector2(32, 32), SliceMode.SIZE_PER_RECT)
    frames = list(map(lambda q: AnimationFrame(q), quads))
    animation = Animation(frames[0:4])

    character.add_behaviour(Animator).animation = animation
    character.add_behaviour(Player)

    character.simulation = simulation

    prop = Node()
    prop.transform.local_scale = pg.Vector2(1.5, 0.5)
    sprite_renderer = prop.add_behaviour(SpriteRenderer)
    sprite_renderer.texture = frames[0].texture
    sprite_renderer.render_layer = -1
    prop.transform.position = pg.Vector2(200, 500)
    prop.simulation = simulation


if __name__ == "__main__":
    init_common()
    pg.init()

    window = pg.display.set_mode((1280, 720))
    simulation = Simulation()
    create_scene(simulation)

    running = True

    last_tick = 0
    while running:
        try:
            this_tick = pg.time.get_ticks()
            dt = (this_tick - last_tick) / 1000.0
            last_tick = this_tick

            for ev in pg.event.get():
                if ev.type == pg.QUIT:
                    running = False

            simulation.update(dt)

            window.fill("white")
            simulation.render()
            pg.display.flip()

        except:
            error_stack_trace = traceback.format_exc()
            print(error_stack_trace, file=stderr)
