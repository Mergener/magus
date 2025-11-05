from client.animation import Animation
from client.behaviours.sprite_renderer import SpriteRenderer
from common.simulation import Behaviour, Node


class Animator(Behaviour):
    def __init__(self, node: Node, animation: Animation):
        super().__init__(node)

        self.animation = animation
        self._frame_idx = 0
        self._accum_time = 0
        self._sprite_renderer: SpriteRenderer | None = None

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
            self._sprite_renderer.texture = current_frame.texture
