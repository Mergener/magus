from enum import Enum

import pygame as pg

from common.behaviours.ui.canvas import Canvas
from common.behaviours.ui.widget import Widget
from common.primitives import Vector2

REPEAT_FLAGS_NONE = 0
REPEAT_FLAGS_REPEAT_X = 1
REPEAT_FLAGS_REPEAT_Y = 2


class UISurface(Widget):
    def on_init(self):
        super().on_init()
        self._new_base_surface: pg.Surface | None
        self._base_surface: pg.Surface | None = None
        self._active_surface: pg.Surface | None = None
        self._tint = pg.Color(255, 255, 255, 255)

        self._cached_scale: Vector2 = self.transform.scale.copy()
        self._cached_rotation: float = self.transform.rotation
        self._cached_ref_resolution: Vector2 | None = None
        self._cached_canvas: Canvas | None = self.canvas
        self._cached_display_size: tuple[int, int] | None = None
        self.surface_scale = Vector2(1, 1)
        self.repeat_flags: int = 0

    @property
    def tint(self):
        return self._tint

    @tint.setter
    def tint(self, value):
        self._tint = value
        self._refresh_active_surface()

    @property
    def surface(self):
        return self._base_surface

    @property
    def transformed_surface(self):
        return self._active_surface

    def set_surface(self, surface: pg.Surface | None):
        self._base_surface = surface
        self._refresh_active_surface()

    def _refresh_active_surface(self):
        if self._base_surface is None:
            self._active_surface = None
            return

        canvas = self.canvas
        if canvas is None:
            return

        transform_scale = self.transform.scale
        scale = transform_scale * canvas.canvas_to_screen_ratio

        if self.repeat_flags & REPEAT_FLAGS_REPEAT_X == 0:
            scale.x *= self.surface_scale.x
        if self.repeat_flags & REPEAT_FLAGS_REPEAT_Y == 0:
            scale.y *= self.surface_scale.y

        # TODO: Texture repeat mode

        new_surface = pg.transform.smoothscale(
            self._base_surface,
            (
                self._base_surface.get_width() * scale.x,
                self._base_surface.get_height() * scale.y,
            ),
        )

        rotation = self.transform.rotation

        new_surface.fill(self._tint, special_flags=pg.BLEND_RGBA_MULT)

        self._active_surface = new_surface

        self._cached_rotation = rotation
        self._cached_scale = transform_scale
        self._cached_ref_resolution = canvas.reference_resolution
        self._cached_canvas = canvas

        if self.game and self.game.display:
            self._cached_display_size = self.game.display.get_size()

    def _must_refresh(self):
        canvas = self.canvas
        if self._cached_canvas is None or canvas is not self._cached_canvas:
            return True

        if (
            canvas is not None
            and canvas.reference_resolution != self._cached_ref_resolution
        ):
            return True

        if self.transform.scale != self._cached_scale:
            return True

        if self.transform.rotation != self._cached_rotation:
            return True

        if self.game and self.game.display:
            current_display_size = self.game.display.get_size()
            if self._cached_display_size != current_display_size:
                return True

        return False

    def on_render(self):
        assert self.game

        if self._must_refresh():
            self._refresh_active_surface()

        canvas = self.canvas
        if self.game.display is None or canvas is None or self._active_surface is None:
            return

        half_surface_size = Vector2(
            self._active_surface.get_width() / 2, self._active_surface.get_height() / 2
        )
        pos = self.transform.position

        sw, sh = self.game.display.get_size()
        screen_point = (
            canvas.canvas_to_screen_point(pos)
            - half_surface_size
            + self.anchor.elementwise() * Vector2(sw, -sh)
        )
        self.game.display.blit(self._active_surface, screen_point)

    @property
    def rect(self):
        canvas = self.canvas
        if (
            not self.game
            or not canvas
            or not self._active_surface
            or not self.game.display
        ):
            return pg.Rect(0, 0, 0, 0)

        half_surface_size = Vector2(
            self._active_surface.get_width() / 2, self._active_surface.get_height() / 2
        )
        pos = self.transform.position

        w, h = canvas.reference_resolution

        return pg.Rect(
            pos + self.anchor.elementwise() * Vector2(w, h) - half_surface_size,
            self._active_surface.get_size(),
        )
