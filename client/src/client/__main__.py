import importlib
import json
import os
import pkgutil
import sys
import traceback
from pathlib import Path
from sys import stderr

import pygame as pg

from client.behaviours.camera import *  # type: ignore
from client.netclient import NetClient
from common.assets import load_node_asset
from common.game import Game
from common.network import auto_resolve_packets

if __name__ == "__main__":
    auto_resolve_packets()
    pg.init()

    game = Game(
        display=pg.display.set_mode((1280, 720)),
        scene=load_node_asset("scenes/game.json"),
        network=NetClient("localhost", 16214),
    )

    running = True
    while running:
        try:
            for ev in pg.event.get():
                if ev.type == pg.QUIT:
                    running = False

            game.iterate()

        except KeyboardInterrupt:
            running = False

        except Exception as e:
            error_stack_trace = traceback.format_exc()
            print(error_stack_trace, file=stderr)

    game.cleanup()
