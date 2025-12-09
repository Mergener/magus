import json
import math

import pygame as pg

from common.behaviour import Behaviour
from common.behaviours.camera import Camera
from game.game_manager import GameManager


class DebugConsole(Behaviour):
    def on_init(self):
        self._font = pg.font.SysFont(
            ["consolas", "monospace", "Courier" "Courier New", "Arial"], 36
        )
        self._fps = 0
        self._texts = ""

    def set_active(self, active: bool):
        assert self.game
        self.visible = active
        # self.game.simulation.render_debug = active

    def on_update(self, dt: float):
        assert self.game
        if self.game.input.is_key_just_released(pg.K_F3):
            self.set_active(not self.visible)
        self._fps = math.floor(1 / max(dt, 0.0000000001))

    def on_tick(self, tick_id: int):
        assert self.game
        sim = self.game.simulation
        if tick_id % int(sim.tick_rate) != 0:
            return

        self._texts = [
            f"FPS: {self._fps} (frametime {sim.last_frame_time * 1000:.3f}ms)",
        ] + [
            f"{topic}: {self.game.profiler.get_last(topic) * 1000:.3f}ms"
            for topic in self.game.profiler.topics
        ]

        camera = self.game.container.get(Camera)
        if camera is not None:
            self._texts.append(f"camera_pos: {camera.transform.position}")

    def on_render(self):
        assert self.game
        texts = self._texts

        screen = self.game.display
        if not screen:
            return
        screen_w, _ = screen.get_size()

        for i, text in enumerate(texts):
            text_surface = self._font.render(text, True, pg.Color(255, 255, 255))
            text_w, text_h = text_surface.get_size()
            pos = (screen_w - text_w - 10, 10 + text_h * i)
            screen.blit(text_surface, pos)
