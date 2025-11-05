from typing import cast

import pygame as pg

from client.behaviours.camera import Camera
from common.simulation import Behaviour, Transform
from common.utils import memberwise_multiply


class SpriteRenderer(Behaviour):
    _dimensions: pg.Vector2 | None
    _texture: pg.Surface | None

    def on_init(self):
        self._texture = None
        self._dimensions = None

    @property
    def texture(self):
        return self._texture

    @texture.setter
    def texture(self, texture: pg.Surface | None):
        self._texture = texture

        if texture is not None:
            self._dimensions = pg.Vector2(texture.get_width(), texture.get_height())
        else:
            self._dimensions = None

    def on_render(self):
        if self.texture is None or self._dimensions is None:
            return

        camera = Camera.main
        if camera is None:
            return

        dim = memberwise_multiply(self._dimensions, self.transform.scale)
        pos = camera.world_to_screen_space(self.transform.position - dim / 2)

        pg.display.get_surface().blit(self.texture, pg.Rect(pos, dim))
