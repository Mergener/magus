from __future__ import annotations

from typing import TYPE_CHECKING

import pygame as pg

if TYPE_CHECKING:
    from common.engine.node import Node

from common.engine.behaviour import Behaviour
from common.engine.utils import memberwise_multiply


class Transform(Behaviour):
    def __init__(self, node: Node):
        super().__init__(node)
        self._local_position = pg.Vector2(0, 0)
        self._local_scale = pg.Vector2(1, 1)
        self._rotation = 0

    @property
    def local_scale(self):
        return self._local_scale

    @local_scale.setter
    def local_scale(self, value: pg.Vector2):
        self._local_scale = value

    @property
    def scale(self):
        scale = self._local_scale
        if self.parent != None:
            scale = memberwise_multiply(self.local_scale, self.parent.transform.scale)
        return scale

    @property
    def local_position(self):
        return self._local_position

    @local_position.setter
    def local_position(self, new_pos: pg.Vector2):
        self._local_position = new_pos

    @property
    def position(self):
        position = self._local_position
        if self.parent is not None:
            position += self.parent.transform.position
        return position

    @position.setter
    def position(self, new_pos: pg.Vector2):
        delta = new_pos - self.position
        self.local_position += delta

    def on_serialize(self, out_dict: dict):
        out_dict["local_position"] = {
            "x": self._local_position.x,
            "y": self._local_position.y,
        }
        out_dict["local_scale"] = {"x": self._local_scale.x, "y": self._local_scale.y}
        out_dict["rotation"] = self._rotation

    def on_deserialize(self, in_dict: dict):
        self._local_position = pg.Vector2(0, 0)
        pos_dict = in_dict.get("local_position")
        if pos_dict:
            self._local_position.x = pos_dict["x"]
            self._local_position.y = pos_dict["y"]

        self._local_scale = pg.Vector2(0, 0)
        scale_dict = in_dict.get("local_scale")
        if scale_dict:
            self._local_scale.x = scale_dict["x"]
            self._local_scale.y = scale_dict["y"]

        self._rotation = in_dict.get("rotation", 0)
