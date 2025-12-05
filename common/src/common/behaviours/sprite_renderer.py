import pygame as pg

from common.behaviour import Behaviour
from common.behaviours.camera import Camera
from common.utils import deserialize_vec2, memberwise_multiply, serialize_vec2


class SpriteRenderer(Behaviour):
    def on_init(self):
        self._texture: pg.Surface | None = None
        self._texture_asset: str | None = None
        self._active_texture: pg.Surface | None = None

        self._dimensions = pg.Vector2(0, 0)
        self._scaled_dimensions = pg.Vector2(0, 0)

        self._cached_scale = self.transform.scale
        self._cached_rot = self.transform.rotation

        self._tint = pg.Color(255, 255, 255, 255)
        self._image_scale = pg.Vector2(1, 1)

    def _refresh_active_texture(self):
        tex = self._texture
        if tex is None:
            self._active_texture = None
            return

        final_scale = memberwise_multiply(self.transform.scale, self.image_scale)

        self._cached_scale = self.transform.scale
        self._cached_rot = self.transform.rotation  # world rotation cached

        self._scaled_dimensions = memberwise_multiply(self._dimensions, final_scale)
        scaled_tex = pg.transform.scale(tex, self._scaled_dimensions)

        rot = self.transform.rotation
        rotated_tex = pg.transform.rotate(scaled_tex, rot)

        tinted = rotated_tex.copy()
        tinted.fill(self.tint, special_flags=pg.BLEND_RGBA_MULT)

        self._active_texture = tinted

    @property
    def image_scale(self):
        return self._image_scale

    @image_scale.setter
    def image_scale(self, value):
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
            self._dimensions = pg.Vector2(tex.get_width(), tex.get_height())
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

        offset = self._active_texture.get_size()
        offset = pg.Vector2(offset[0], offset[1])

        pos = camera.world_to_screen_space(self.transform.position - offset / 2)

        self.game.display.blit(self._active_texture, pos)

    def on_serialize(self, out_dict):
        out_dict["texture"] = self._texture_asset
        out_dict["image_scale"] = serialize_vec2(self.image_scale)

    def on_deserialize(self, in_dict):
        self._texture_asset = in_dict["texture"]
        self.image_scale = deserialize_vec2(
            in_dict.get("image_scale"), pg.Vector2(1, 1)
        )

        if not isinstance(self._texture_asset, str):
            self._texture_asset = None
