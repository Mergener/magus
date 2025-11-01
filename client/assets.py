import os
import pygame as pg

def load_image_asset(path: str) -> pg.Surface:
    return pg.image.load(os.path.abspath(os.path.join("assets", path)))