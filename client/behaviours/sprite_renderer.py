from typing import cast

import pygame as pg

from client.behaviours.camera import Camera
from common.simulation import Behaviour, Transform
from common.utils import memberwise_multiply


class SpriteRenderer(Behaviour):
    _texture: pg.Surface | None
    _dimensions: pg.Vector2
    _scaled_texture: pg.Surface | None
    _scaled_dimensions: pg.Vector2
    _cached_scale: pg.Vector2

    def on_init(self):
        self._texture = None
        self._scaled_texture = None
        self._dimensions = pg.Vector2(0, 0)
        self._cached_scale = self.transform.scale
        self._scaled_dimensions = pg.Vector2(0, 0)

    def _update_scaled_texture(self):
        if self._texture is None:
            self._scaled_texture = None
            self._scaled_dimensions = pg.Vector2(0, 0)
            return

        scale = self.transform.scale
        self._cached_scale = scale
        self._scaled_dimensions = memberwise_multiply(self._dimensions, scale)
        self._scaled_texture = pg.transform.scale(
            self._texture, self._scaled_dimensions
        )

    @property
    def texture(self):
        return self._texture

    @texture.setter
    def texture(self, texture: pg.Surface | None):
        self._texture = texture

        if texture is not None:
            self._dimensions = pg.Vector2(texture.get_width(), texture.get_height())
        else:
            self._dimensions = pg.Vector2(0, 0)

        self._update_scaled_texture()

    def on_render(self):
        if self._scaled_texture is None:
            return

        if self._cached_scale != self.transform.scale:
            self._update_scaled_texture()

        camera = Camera.main
        if camera is None:
            return

        dim = memberwise_multiply(self._dimensions, self.transform.scale)
        pos = camera.world_to_screen_space(self.transform.position - dim / 2)

        pg.display.get_surface().blit(
            self._scaled_texture, pg.Rect(pos, self._scaled_dimensions)
        )
