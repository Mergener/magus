import traceback
from sys import stderr

import pygame as pg

from client.netclient import NetClient
from client.scenes.game_scene import make_game_scene
from common import init_common
from common.engine.game import Game

if __name__ == "__main__":
    init_common()
    pg.init()

    game = Game(
        scene=make_game_scene(),
        network=NetClient("localhost", 16214),
        display=pg.display.set_mode((1280, 720)),
    )

    running = True
    while running:
        try:
            for ev in pg.event.get():
                if ev.type == pg.QUIT:
                    running = False

            game.iterate()

        except:
            error_stack_trace = traceback.format_exc()
            print(error_stack_trace, file=stderr)

    game.cleanup()
