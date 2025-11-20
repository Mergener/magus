import json

import pygame as pg

from common.behaviour import Behaviour


class DebugConsole(Behaviour):
    def on_start(self):
        self._texture = None
        mono_name = pg.font.match_font("consolas, courier, couriernew, monospace")
        self._font = pg.font.Font(mono_name, 9)
        self.margin = 2

    def set_active(self, active: bool):
        self.receive_updates = active
        self.visible = active

    def on_tick(self, tick_id: int):
        assert self.game
        text = json.dumps(self.game.scene.serialize(), indent=2)
        self._lines = text.split("\n")

        self._rendered = [
            self._font.render(line, True, (255, 255, 255)) for line in self._lines
        ]

        self._max_width = (
            max(surf.get_width() for surf in self._rendered) if self._rendered else 0
        )

    def on_render(self):
        assert self.game and self.game.display

        if not hasattr(self, "_rendered") or not self._rendered:
            return

        sw, sh = self.game.display.get_size()

        x = sw - self._max_width - self.margin
        y = self.margin

        for surf in self._rendered:
            self.game.display.blit(surf, (x, y))
            y += surf.get_height()
