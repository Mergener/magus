import os
import sys

import pygame as pg


def resource_path(relative_path: str) -> str:
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, "assets", relative_path)


def load_image_asset(path: str) -> pg.Surface:
    full_path = resource_path(path)
    return pg.image.load(full_path).convert_alpha()
