import pygame as pg

from common.behaviour import Behaviour


class Canvas(Behaviour):
    reference_resolution: pg.Vector2

    def on_init(self):
        self.reference_resolution = pg.Vector2(1680, 1050)
