from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import pygame as pg

from common.behaviour import Behaviour

if TYPE_CHECKING:
    from common.behaviours.ui.canvas import Canvas
from common.primitives import Vector2


class Widget(Behaviour, ABC):
    def on_init(self):
        self._anchor = Vector2(0.5, 0.5)

    @property
    @abstractmethod
    def rect(self) -> pg.Rect:
        pass

    @property
    def anchor(self):
        return self._anchor

    @anchor.setter
    def anchor(self, value: Vector2):
        self._anchor = value

    @property
    def canvas(self):
        from common.behaviours.ui.canvas import Canvas

        parent = self.parent
        while parent is not None:
            canvas = parent.get_behaviour(Canvas)
            if canvas:
                return canvas
            parent = parent.parent
        return None

    def on_serialize(self, out_dict: dict):
        out_dict["anchor"] = self.anchor.serialize()

    def on_deserialize(self, in_dict: dict):
        self.anchor = Vector2().deserialize(in_dict.get("anchor"))
