import importlib
import json
import os
import pkgutil
import sys
import traceback
from pathlib import Path
from sys import stderr

import pygame as pg

from client.netclient import NetClient
from common.assets import load_node_asset
from common.behaviours.camera import *  # type: ignore
from common.behaviours.ui.canvas import Canvas
from common.behaviours.ui.ui_button import UIButton
from common.behaviours.ui.ui_label import UILabel
from common.game import Game
from common.node import Node

if __name__ == "__main__":
    pg.init()

    game = Game(
        display=pg.display.set_mode((1280, 720), pg.RESIZABLE),
        scene=load_node_asset("scenes/client/lobby.json"),
        network=NetClient("localhost", 16214),
        global_object=load_node_asset("client_global_object.json"),
    )

    while not game.stopped:
        try:
            game.iterate()
            game.handle_pygame_events(pg.event.get())

        except KeyboardInterrupt:
            game.quit()

        except Exception as e:
            error_stack_trace = traceback.format_exc()
            print(error_stack_trace, file=stderr)

    game.cleanup()
