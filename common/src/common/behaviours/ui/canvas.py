from __future__ import annotations

from enum import Enum

import pygame as pg

from common.behaviour import Behaviour
from common.primitives import Vector2


class Canvas(Behaviour):
    reference_resolution: Vector2

    def on_init(self):
        self.reference_resolution = Vector2(1680, 1050)

    def canvas_to_screen_point(self, point: Vector2):
        if self.game is None or self.game.display is None:
            return point

        rrw, rrh = self.reference_resolution
        sw, sh = self.game.display.get_size()

        return Vector2(point.x * (sw / rrw), (rrh - point.y) * (sh / rrh))

    def screen_to_canvas_point(self, point: Vector2):
        if self.game is None or self.game.display is None:
            return point

        rrw, rrh = self.reference_resolution
        sw, sh = self.game.display.get_size()

        return Vector2(point.x * (rrw / sw), rrh - (point.y * (rrh / sh)))

    def canvas_to_screen_rect(self, rect: pg.Rect):
        if self.game is None or self.game.display is None:
            return rect

        sw, sh = self.game.display.get_size()
        scale_ratio = self._canvas_to_screen_ratio(sw, sh)
        x, y = rect.topleft

        return pg.Rect(
            self.canvas_to_screen_point(Vector2(x, y)),
            Vector2(rect.w * scale_ratio, rect.h * scale_ratio),
        )

    def screen_to_canvas_rect(self, rect: pg.Rect):
        if self.game is None or self.game.display is None:
            return rect

        sw, sh = self.game.display.get_size()
        scale_ratio = self._screen_to_canvas_ratio(sw, sh)
        x, y = rect.topleft

        return pg.Rect(
            self.screen_to_canvas_point(Vector2(x, y)),
            Vector2(rect.w * scale_ratio, rect.h * scale_ratio),
        )

    def _canvas_to_screen_ratio(self, sw: int, sh: int):
        w_ratio = sw / self.reference_resolution.x
        h_ratio = sh / self.reference_resolution.y

        return w_ratio if abs(w_ratio - 1) > abs(h_ratio - 1) else h_ratio

    def _screen_to_canvas_ratio(self, sw: int, sh: int):
        return 1 / self._canvas_to_screen_ratio(sw, sh)

    @property
    def canvas_to_screen_ratio(self):
        if not self.game or not self.game.display:
            return 1
        sw, sh = self.game.display.get_size()
        return self._canvas_to_screen_ratio(sw, sh)

    @property
    def screen_to_canvas_ratio(self):
        if not self.game or not self.game.display:
            return 1
        sw, sh = self.game.display.get_size()
        return self._screen_to_canvas_ratio(sw, sh)
