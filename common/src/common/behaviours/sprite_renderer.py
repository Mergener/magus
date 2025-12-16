import math
from dataclasses import dataclass

import pygame as pg

from common.behaviour import Behaviour
from common.behaviours.camera import Camera
from common.primitives import Vector2


@dataclass
class _TextureCacheEntry:
    scale: Vector2
    rotation: float
    tint: pg.Color
    base_texture: pg.Surface
    transformed_texture: pg.Surface


class SpriteRenderer(Behaviour):
    def on_init(self):
        self._texture: pg.Surface | None = None
        self._texture_asset: str | None = None
        self._active_texture: pg.Surface | None = None

        self._dimensions = Vector2(0, 0)
        self._scaled_dimensions = Vector2(0, 0)

        self._tint = pg.Color(255, 255, 255, 255)
        self._texture_cache_size = 3
        self._texture_cache: list[_TextureCacheEntry] | None = []
        self._image_scale = Vector2(1, 1)

        self._last_scale = self.transform.scale.copy()
        self._last_rotation = float(self.transform.rotation)
        self._last_screen_size = (0, 0)
        self._last_camera_scale = 1

    def _refresh_active_texture(self):
        base_texture = self._texture
        if base_texture is None:
            self._active_texture = None
            return

        scale = self.transform.scale.elementwise() * self.image_scale
        if self.game:
            camera = self.game.container.get(Camera)
            if camera is not None:
                scale *= camera.world_to_screen_scale()
        rotation = self.transform.rotation
        tint = self.tint

        if self._texture_cache is not None:
            for i, e in enumerate(self._texture_cache):
                if (
                    e.base_texture is base_texture
                    and e.scale.roughly_equals(scale)
                    and (abs(e.rotation - rotation) < 0.1)
                    and e.tint == tint
                ):
                    self._active_texture = e.transformed_texture
                    self._texture_cache.append(self._texture_cache.pop(i))
                    return

        transformed_tex = pg.transform.smoothscale_by(base_texture, scale)
        transformed_tex = pg.transform.rotate(transformed_tex, rotation)
        transformed_tex.fill(self.tint, special_flags=pg.BLEND_RGBA_MULT)
        self._active_texture = transformed_tex

        if self._texture_cache is None:
            return

        self._texture_cache.append(
            _TextureCacheEntry(scale, rotation, tint, base_texture, transformed_tex)
        )
        if len(self._texture_cache) > self._texture_cache_size:
            del self._texture_cache[0]

    @property
    def texture_cache_size(self):
        return self._texture_cache_size

    @texture_cache_size.setter
    def texture_cache_size(self, value: int):
        self._texture_cache_size = value
        if value == 0:
            self._texture_cache = None
        elif self._texture_cache is None:
            self._texture_cache = []
        elif value < len(self._texture_cache):
            self._texture_cache = self._texture_cache[
                (len(self._texture_cache) - value) :
            ]

    @property
    def image_scale(self):
        return self._image_scale

    @image_scale.setter
    def image_scale(self, value: Vector2):
        self._image_scale = value
        self._refresh_active_texture()

    @property
    def tint(self):
        return self._tint

    @tint.setter
    def tint(self, value):
        self._tint = value
        self._refresh_active_texture()

    @property
    def texture(self):
        return self._texture

    @texture.setter
    def texture(self, tex):
        self._texture = tex

        if tex:
            self._dimensions = Vector2(tex.get_width(), tex.get_height())
        else:
            self._dimensions = Vector2(0, 0)

        self._refresh_active_texture()

    def on_render(self):
        assert self.game
        if self._active_texture is None:
            return

        camera = self.game.container.get(Camera)
        if camera is None or self.game is None or self.game.display is None:
            return

        needs_refresh = False
        if not self.transform.scale.roughly_equals(self._last_scale):
            needs_refresh = True
            self._last_scale.x = self.transform.scale.x
            self._last_scale.y = self.transform.scale.y

        cur_rot = float(self.transform.rotation)
        if abs(cur_rot - self._last_rotation) > 0.1:
            needs_refresh = True
            self._last_rotation = cur_rot

        if self.game and self.game.display:
            screen_size = self.game.display.get_size()
            if screen_size != self._last_screen_size:
                needs_refresh = True
                self._last_screen_size = screen_size

        if camera is not None:
            cam_scale = camera.world_to_screen_scale()
            if abs(cam_scale - self._last_camera_scale) > 0.1:
                needs_refresh = True
                self._last_camera_scale = cam_scale

        if needs_refresh:
            self._refresh_active_texture()

        half_size = Vector2(self._active_texture.get_size()) / 2
        pos = camera.world_to_screen_space(self.transform.position) - half_size

        self.game.display.blit(self._active_texture, pos)

    def on_serialize(self, out_dict):
        out_dict["texture"] = self._texture_asset
        out_dict["image_scale"] = self.image_scale.serialize()

    def on_deserialize(self, in_dict):
        self._texture_asset = in_dict["texture"]
        self.image_scale.deserialize(in_dict.get("image_scale"), Vector2(1, 1))

        if not isinstance(self._texture_asset, str):
            self._texture_asset = None
