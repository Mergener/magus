from common.behaviour import Behaviour
from common.behaviours.camera import Camera
from common.primitives import Vector2


class PlayerCamera(Behaviour):
    def on_init(self):
        self.edge_pan_speed = 1000

    def on_start(self):
        assert self.game
        self._camera = self.game.container.get(Camera)

    def on_update(self, dt: float):
        assert self.game
        if not self._camera:
            return

        if self.game.display:
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

    def on_serialize(self, out_dict: dict):
        out_dict["edge_pan_speed"] = self.edge_pan_speed

    def on_deserialize(self, in_dict: dict):
        self.edge_pan_speed = in_dict.get("edge_pan_speed", 1000)


def _relative_position(pos: Vector2, size: tuple[int, int]):
    return Vector2(pos.x / size[0], (size[1] - pos.y) / size[1])
