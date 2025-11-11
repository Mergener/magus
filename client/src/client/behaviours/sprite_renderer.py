from typing import cast

import pygame as pg

from client.behaviours.camera import Camera
from common.engine.behaviour import Behaviour
from common.engine.utils import memberwise_multiply


class SpriteRenderer(Behaviour):
    _texture: pg.Surface | None
    _dimensions: pg.Vector2
    _active_texture: pg.Surface | None
    _scaled_dimensions: pg.Vector2
    _cached_scale: pg.Vector2
    _tint: pg.Color

    def on_init(self):
        self._texture = None
        self._active_texture = None
        self._dimensions = pg.Vector2(0, 0)
        self._cached_scale = self.transform.scale
        self._scaled_dimensions = pg.Vector2(0, 0)
        self._tint = pg.Color(255, 255, 255, 255)

    def _refresh_active_texture(self):
        if self._texture is None:
            self._active_texture = None
            return

        scale = self.transform.scale
        self._cached_scale = scale
        self._scaled_dimensions = memberwise_multiply(self._dimensions, scale)
        scaled_texture = pg.transform.scale(self._texture, self._scaled_dimensions)

        tinted_texture = scaled_texture.copy()
        tinted_texture.fill(self.tint, special_flags=pg.BLEND_RGBA_MULT)
        self._active_texture = tinted_texture

    @property
    def tint(self):
        return self._tint

    @tint.setter
    def tint(self, value: pg.Color):
        self._tint = value
        self._refresh_active_texture()

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

        self._refresh_active_texture()

    def on_render(self):
        if self._active_texture is None:
            return

        if self._cached_scale != self.transform.scale:
            self._refresh_active_texture()

        camera = Camera.main
        if camera is None or self.game is None or self.game.screen is None:
            return

        dim = memberwise_multiply(self._dimensions, self.transform.scale)
        pos = camera.world_to_screen_space(self.transform.position - dim / 2)

        self.game.screen.blit(
            self._active_texture, pg.Rect(pos, self._scaled_dimensions)
        )
