import pygame as pg

from common.behaviour import Behaviour
from common.behaviours.camera import Camera
from common.primitives import Vector2
from common.utils import notnull
from game.game_manager import GameManager, RoundFinished, RoundStarting


class PlayerCamera(Behaviour):
    def on_init(self):
        self.edge_pan_speed = 1000

    def on_start(self):
        assert self.game
        self._camera = self.game.container.get(Camera)
        self._round_start_handler = self.game.network.listen(
            RoundStarting, lambda _, __: self._pan_camera_to_mage()
        )
        self._round_finish_handler = self.game.network.listen(
            RoundFinished, lambda _, __: self._pan_camera_to_mage()
        )

    def on_destroy(self):
        assert self.game
        self.game.network.unlisten(RoundStarting, self._round_start_handler)
        self.game.network.unlisten(RoundFinished, self._round_finish_handler)

    def on_update(self, dt: float):
        assert self.game
        if not self._camera:
            return

        if not self.game.display:
            return

        if self.game.input.is_mouse_button_pressed(pg.BUTTON_MIDDLE):
            # Mouse drag
            motion = (
                Vector2(1, -1).elementwise()
                * self.game.input.mouse_delta
                * self._camera.screen_to_world_scale()
            )
            self._camera.transform.local_position -= motion
        else:
            # Edge pan
            mouse_pos = self.game.input.mouse_pos
            screen_size = self.game.display.get_size()
            rel_pos = _relative_position(mouse_pos, screen_size)

            x_motion = 0
            y_motion = 0

            if rel_pos.x <= 0.01:
                x_motion = -1
            elif rel_pos.x >= 0.99:
                x_motion = 1

            if rel_pos.y <= 0.01:
                y_motion = -1
            elif rel_pos.y >= 0.99:
                y_motion = 1

            if x_motion != 0 or y_motion != 0:
                self._camera.transform.local_position += (
                    Vector2(x_motion, y_motion).normalize() * self.edge_pan_speed * dt
                )

        if self.game.input.is_key_just_pressed(pg.K_SPACE):
            self._pan_camera_to_mage()

    def on_serialize(self, out_dict: dict):
        out_dict["edge_pan_speed"] = self.edge_pan_speed

    def on_deserialize(self, in_dict: dict):
        self.edge_pan_speed = in_dict.get("edge_pan_speed", 1000)

    def _pan_camera_to_mage(self):
        assert self.game
        game_mgr = self.game.container.get(GameManager)
        if game_mgr is not None:
            local_player = game_mgr.get_local_player()
            if local_player is None:
                return
            mage = local_player.mage
            if mage is not None:
                self._camera.transform.position = mage.transform.position


def _relative_position(pos: Vector2, size: tuple[int, int]):
    return Vector2(pos.x / size[0], (size[1] - pos.y) / size[1])


def _relative_delta(delta: Vector2, size: tuple[int, int]):
    return Vector2(delta.x / size[0], -delta.y / size[1])
