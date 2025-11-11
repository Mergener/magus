import traceback
from sys import stderr

import pygame as pg

from client.netclient import NetClient
from client.scenes.game_scene import make_game_scene
from common.engine.game import Game
from common.engine.network import auto_resolve_packets

if __name__ == "__main__":
    auto_resolve_packets()
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
