from enum import Enum

import pygame as pg

from common.assets import ImageAsset, load_image_asset
from common.behaviours.ui.ui_surface import UISurface


class UIImage(UISurface):
    def on_init(self):
        super().on_init()

        self._image_path: str | None = None
        self._image_asset: ImageAsset | None = None
        self._tint_color: pg.Color = pg.Color(255, 255, 255, 255)

    def _refresh_image_surface(self):
        if not self._image_path:
            self.set_surface(None)
            return

        try:
            self._image_asset = load_image_asset(self._image_path)
            surface = self._image_asset.pygame_surface.copy()

            if self._tint_color != pg.Color(255, 255, 255, 255):
                tint_surface = pg.Surface(surface.get_size(), pg.SRCALPHA)
                tint_surface.fill(self._tint_color)
                surface.blit(tint_surface, (0, 0), special_flags=pg.BLEND_RGBA_MULT)

            self.set_surface(surface)
        except Exception as e:
            print(f"Failed to load image: {e}")
            self.set_surface(None)

    @property
    def image_path(self):
        return self._image_path

    @image_path.setter
    def image_path(self, value: str | None):
        self._image_path = value
        self._refresh_image_surface()

    @property
    def tint_color(self):
        return self._tint_color

    @tint_color.setter
    def tint_color(self, value: pg.Color | tuple):
        if isinstance(value, tuple):
            self._tint_color = pg.Color(*value)
        else:
            self._tint_color = value
        self._refresh_image_surface()

    @property
    def image_asset(self):
        return self._image_asset

    def on_serialize(self, out_dict: dict):
        super().on_serialize(out_dict)
        out_dict["image"] = self._image_path
        out_dict["tint"] = {
            "r": self._tint_color.r,
            "g": self._tint_color.g,
            "b": self._tint_color.b,
            "a": self._tint_color.a,
        }
        out_dict["surface_scale"] = {
            "x": self.surface_scale.x,
            "y": self.surface_scale.y,
        }

    def on_deserialize(self, in_dict: dict):
        super().on_deserialize(in_dict)
        self._image_path = in_dict.get("image", None)

        tint_dict = in_dict.get("tint")
        if tint_dict:
            self._tint_color = pg.Color(
                tint_dict.get("r", 255),
                tint_dict.get("g", 255),
                tint_dict.get("b", 255),
                tint_dict.get("a", 255),
            )
        else:
            self._tint_color = pg.Color(255, 255, 255, 255)

        surf_scale_dict = in_dict.get("surface_scale")
        if surf_scale_dict:
            self.surface_scale = pg.Vector2(
                surf_scale_dict.get("x", 0), surf_scale_dict.get("y", 0)
            )

        self._refresh_image_surface()
