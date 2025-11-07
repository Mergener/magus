from typing import ClassVar, Self

import pygame as pg

from common.simulation import Behaviour


class Camera(Behaviour):
    main: ClassVar[Self | None] = None

    def on_start(self):
        if Camera.main is None:
            Camera.main = self

    def world_to_screen_space(self, point: pg.Vector2):
        screen_rect = pg.display.get_surface().get_rect()
        screen_x = point.x + screen_rect.centerx - self.transform.position.x
        screen_y = point.y + screen_rect.centery - self.transform.position.y
        return pg.Vector2(screen_x, screen_y)

    def screen_to_world_space(self, point: pg.Vector2):
        screen_rect = pg.display.get_surface().get_rect()
        world_x = point.x - screen_rect.centerx + self.transform.position.x
        world_y = point.y - screen_rect.centery + self.transform.position.y
        return pg.Vector2(world_x, world_y)
