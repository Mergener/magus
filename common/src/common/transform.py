import pygame as pg

from common.behaviour import Behaviour
from common.node import Node
from common.utils import memberwise_multiply


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
