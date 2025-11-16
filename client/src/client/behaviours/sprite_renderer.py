import math
from typing import cast

import pygame as pg

from client.behaviours.camera import Camera
from common.assets import load_image_asset
from common.behaviour import Behaviour
from common.transform import Transform
from common.utils import memberwise_multiply


class SpriteRenderer(Behaviour):
    _texture: pg.Surface | None
    _dimensions: pg.Vector2
    _active_texture: pg.Surface | None
    _scaled_dimensions: pg.Vector2
    _cached_scale: pg.Vector2
    _cached_rot: float
    _tint: pg.Color
    _texture_asset: str | None

    def on_init(self):
        self._texture = None
        self._texture_asset = None
        self._active_texture = None
        self._dimensions = pg.Vector2(0, 0)
        self._cached_scale = self.transform.scale
        self._cached_rot = self.transform.rotation
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

        rotated_texture = pg.transform.rotate(scaled_texture, self.transform.rotation)

        tinted_texture = rotated_texture.copy()
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

        if (
            self._cached_scale != self.transform.scale
            or self._cached_rot != self.transform.rotation
        ):
            self._refresh_active_texture()

        camera = Camera.main
        if camera is None or self.game is None or self.game.display is None:
            return

        offset = memberwise_multiply(self._dimensions, self.transform.scale)
        if self.parent:
            offset.rotate(self.parent.transform.rotation)

        pos = camera.world_to_screen_space(self.transform.position - offset / 2)

        self.game.display.blit(
            self._active_texture, pg.Rect(pos, self._scaled_dimensions)
        )

    def on_serialize(self, out_dict: dict):
        out_dict["texture"] = self._texture_asset

    def on_deserialize(self, in_dict: dict):
        self._texture_asset = in_dict["texture"]
        if type(self._texture_asset) != str:
            self._texture_asset = None
            return
