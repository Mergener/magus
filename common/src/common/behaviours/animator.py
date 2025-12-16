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
        self._current_animation_name: str | None = "idle"
        self._queue: list[str] = []
        self.animations = {}

    @property
    def current_animation_name(self):
        return self._current_animation_name

    def on_pre_start(self):
        self._sprite_renderer = self.node.get_or_add_behaviour(SpriteRenderer)

    def on_start(self):
        if "idle" in self.animations:
            self.play("idle")

    def on_update(self, dt):
        if self._current_animation is None:
            return

        current_frame = self._current_animation.frames[self._frame_idx]

        interval = 1 / (self._current_animation.fps * current_frame.speed)
        self._accum_time += dt

        if self._accum_time > interval:
            self._accum_time -= interval
            self._frame_idx += 1
            if self._frame_idx >= len(self._current_animation.frames):
                self._frame_idx = 0
                if len(self._queue) > 0:
                    self.play(self._queue.pop(), clear_queue=False)
                    return
            current_frame = self._current_animation.frames[self._frame_idx]

            if self._sprite_renderer is not None:
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

    def play(
        self, animation_name: str, force_restart: bool = False, clear_queue: bool = True
    ):
        anim = self.animations.get(animation_name)

        if anim is None and animation_name != "null":
            print(f"Warn: Calling play() in unregistered animation {animation_name}")
        elif animation_name == "null" and self._sprite_renderer is not None:
            self._sprite_renderer.texture = None

        if self._sprite_renderer is not None and anim is not None:
            self._sprite_renderer.texture_cache_size = max(
                len(anim.frames), self._sprite_renderer.texture_cache_size
            )

        if clear_queue:
            self._queue.clear()

        if not force_restart and anim == self._current_animation:
            return

        self._current_animation_name = animation_name
        self._current_animation = anim
        self._accum_time = 0
        self._frame_idx = 0

    def enqueue(self, animation_name: str):
        self._queue.insert(0, animation_name)
