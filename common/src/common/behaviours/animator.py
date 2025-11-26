from common.animation import Animation
from common.assets import load_animation_asset
from common.behaviour import Behaviour
from common.behaviours.sprite_renderer import SpriteRenderer
from common.node import Node


class Animator(Behaviour):
    animations: dict[str, Animation]
    _sprite_renderer: SpriteRenderer | None
    _frame_idx: int
    _accum_time: float

    def on_init(self):
        self._frame_idx = 0
        self._accum_time = 0
        self._sprite_renderer = None
        self._current_animation: Animation | None = None
        self.animations = {}

    def on_start(self):
        self._sprite_renderer = self.node.get_or_add_behaviour(SpriteRenderer)

        if "idle" in self.animations:
            self.play("idle")

    def on_update(self, dt):
        if self._current_animation is None or self._sprite_renderer is None:
            return

        print(self.transform.position)

        current_frame = self._current_animation.frames[self._frame_idx]

        interval = 1 / (self._current_animation.fps * current_frame.speed)
        self._accum_time += dt

        if self._accum_time > interval:
            self._accum_time -= interval
            self._frame_idx = (self._frame_idx + 1) % len(
                self._current_animation.frames
            )
            current_frame = self._current_animation.frames[self._frame_idx]
            self._sprite_renderer.texture = current_frame.image.pygame_surface

    def on_serialize(self, out_dict: dict):
        out_dict["animations"] = {}
        for k, a in self.animations.items():
            if a.path is not None and a.path != "":
                out_dict["animations"][k] = a.path

    def on_deserialize(self, in_dict: dict):
        dict_anim = in_dict.get("animations", {})
        for k, a in dict_anim.items():
            if a is not None and a != "":
                self.animations[k] = load_animation_asset(a)

    def play(self, animation_name: str, force_restart: bool = False):
        anim = self.animations.get(animation_name)
        if anim == None:
            print(f"Warn: Calling play() in unregistered animation {animation_name}")

        if not force_restart and anim == self._current_animation:
            return
        self._current_animation = anim
        self._accum_time = 0
        self._frame_idx = 0
