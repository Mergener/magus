from client.behaviours.sprite_renderer import SpriteRenderer
from common.animation import Animation
from common.assets import load_animation_asset
from common.behaviour import Behaviour
from common.node import Node


class Animator(Behaviour):
    animation: Animation | None
    _sprite_renderer: SpriteRenderer | None
    _frame_idx: int
    _accum_time: float

    def on_init(self):
        self._frame_idx = 0
        self._accum_time = 0
        self.animation = None
        self._sprite_renderer = None

    def on_start(self):
        self._sprite_renderer = self.node.get_behaviour(SpriteRenderer)

    def on_update(self, dt):
        if self.animation is None or self._sprite_renderer is None:
            return

        current_frame = self.animation.frames[self._frame_idx]

        interval = 1 / (self.animation.fps * current_frame.speed)
        self._accum_time += dt

        if self._accum_time > interval:
            self._accum_time -= interval
            self._frame_idx = (self._frame_idx + 1) % len(self.animation.frames)
            current_frame = self.animation.frames[self._frame_idx]
            self._sprite_renderer.texture = current_frame.image.pygame_surface

    def on_serialize(self, out_dict: dict):
        if self.animation:
            out_dict["animation"] = self.animation.path

    def on_deserialize(self, in_dict: dict):
        dict_anim = in_dict.get("animation", "")
        self.animation = load_animation_asset(dict_anim)
