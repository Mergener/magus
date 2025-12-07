from typing import ClassVar, Self

import pygame as pg

from common.behaviour import Behaviour
from common.primitives import Vector2


class Camera(Behaviour):
    main: ClassVar[Self | None] = None
    view_rect_size: Vector2
    view_rect_relative_offset: Vector2

    def on_init(self):
        self.view_rect_size = Vector2(1920, 1080)

    def on_pre_start(self):
        if Camera.main is None:
            Camera.main = self

    def world_to_screen_space(self, point: Vector2):
        if self.game is None or self.game.display is None:
            return Vector2(0, 0)

        sw, sh = self.game.display.get_size()
        screen_x = (
            point.x - self.transform.position.x
        ) * self.world_to_screen_scale() + sw / 2
        screen_y = (
            point.y - self.transform.position.y
        ) * self.world_to_screen_scale() + sh / 2
        return Vector2(screen_x, sh - screen_y)

    def screen_to_world_space(self, point: Vector2):
        if self.game is None or self.game.display is None:
            return Vector2(0, 0)

        sw, sh = self.game.display.get_size()
        world_x = (
            point.x - sw / 2
        ) * self.screen_to_world_scale() + self.transform.position.x
        world_y = (
            (sh - point.y) - sh / 2
        ) * self.screen_to_world_scale() + self.transform.position.y
        return Vector2(world_x, world_y)

    def world_to_screen_scale(self, x: float = 1):
        if self.game is None or self.game.display is None:
            return 1

        sw, sh = self.game.display.get_size()
        w_ratio = sw / self.view_rect_size.x
        h_ratio = sh / self.view_rect_size.y

        return w_ratio if abs(w_ratio - 1) > abs(h_ratio - 1) else h_ratio

    def screen_to_world_scale(self, x: float = 1):
        return 1 / self.world_to_screen_scale()
