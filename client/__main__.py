import pygame as pg
import traceback

from sys import stderr

from client.animation import Animation, AnimationFrame, SliceMode, slice_image
from client.assets import load_image_asset
from client.behaviours.animator import Animator
from client.behaviours.camera import Camera
from client.behaviours.player import Player
from client.behaviours.sprite_renderer import SpriteRenderer
from client.netclient import NetClient
from common import init_common
from common.enums import DeliveryMode
from common.simulation import Node, Simulation


def create_scene(simulation) -> Node:
    camera = Node()
    camera.simulation = simulation
    camera.add_behaviour(Camera())

    character = Node()

    img = load_image_asset("img/mage.png")

    sprite_renderer = SpriteRenderer(img)
    character.add_behaviour(sprite_renderer)

    quads = slice_image(img, pg.Vector2(32, 32), SliceMode.SIZE_PER_RECT)
    frames = list(map(lambda q: AnimationFrame(q), quads))
    animation = Animation(frames[0:4])

    character.add_behaviour(Animator(animation))
    character.add_behaviour(Player())

    character.simulation = simulation


if __name__ == "__main__":
    init_common()
    pg.init()

    window = pg.display.set_mode((1280, 720))
    # net_client = NetClient("localhost", 9999)
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

            window.fill((0, 0, 0))
            simulation.render()
            pg.display.flip()

        except:
            error_stack_trace = traceback.format_exc()
            print(error_stack_trace, file=stderr)
