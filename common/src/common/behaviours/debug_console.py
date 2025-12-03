import json

import pygame as pg

from common.behaviour import Behaviour


class DebugConsole(Behaviour):
    def set_active(self, active: bool):
        assert self.game
        self.visible = active
        self.game.simulation.render_debug = active

    def on_update(self, dt: float):
        assert self.game
        if self.game.input.is_key_just_released(pg.K_F3):
            self.set_active(not self.visible)
