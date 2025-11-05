from typing import cast
import pygame as pg

from client.behaviours.camera import Camera
from common.simulation import Behaviour, Transform


class SpriteRenderer(Behaviour):
    _dimensions: pg.Vector2 | None
    _texture: pg.Surface | None

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

        dim = self._dimensions
        pos = cast(Transform, self.transform).position - dim / 2

        pg.display.get_surface().blit(self.texture, pg.Rect(pos, dim))
