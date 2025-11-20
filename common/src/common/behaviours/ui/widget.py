from abc import ABC
from typing import TYPE_CHECKING

import pygame as pg

from common.behaviour import Behaviour

if TYPE_CHECKING:
    from common.behaviours.ui.canvas import Canvas


class Widget(Behaviour, ABC):
    def on_init(self):
        self._anchor = pg.Vector2(0.5, 0.5)

    @property
    def render_layer(self):
        return super().render_layer + 1048576

    @property
    def anchor(self):
        return self._anchor

    @anchor.setter
    def anchor(self, value: pg.Vector2):
        self._anchor = value

    @property
    def canvas(self):
        parent = self.parent
        while parent is not None:
            canvas = parent.get_behaviour(Canvas)
            if canvas:
                return canvas
            parent = parent.parent
        return None
