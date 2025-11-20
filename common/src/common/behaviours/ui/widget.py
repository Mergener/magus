from abc import ABC

from common.behaviour import Behaviour


class Widget(Behaviour, ABC):
    def on_init(self):
        pass

    @property
    def render_layer(self):
        return super().render_layer + 1048576
