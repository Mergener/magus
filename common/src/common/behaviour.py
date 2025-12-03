from abc import ABC
from typing import TYPE_CHECKING, Any

from common.node import Node

if TYPE_CHECKING:
    from common.behaviours.transform import Transform


class Behaviour(ABC):
    def __init__(self, node: Node):
        self._started = False
        self._node = node

        self._receive_updates = True
        self._visible = True
        self._render_layer = 0

        self.skip_serialization = False

        # Force property refresh
        self.visible = self._visible
        self.receive_updates = self._receive_updates

        self.on_init()

    def on_init(self) -> Any:
        """Called upon behaviour default construction."""
        pass

    def on_pre_start(self) -> Any:
        """Called as soon as the behaviour is materialized in a simulation."""
        pass

    def on_start(self) -> Any:
        """Called when the behaviour is materialized in a simulation, after on_pre_start."""
        pass

    def on_update(self, dt: float) -> Any:
        """Called every simulation frame, with variable interval."""
        pass

    def on_tick(self, tick_id: int) -> Any:
        """Called every simulation tick, with fixed interval."""
        pass

    def on_destroy(self) -> Any:
        """Called when this behaviour or its corresponding node gets destroyed."""
        pass

    def on_render(self) -> Any:
        """Called every simulation render cycle."""
        pass

    def on_debug_render(self) -> Any:
        """Called every simulation render cycle if RENDER_DEBUG is True."""

    def on_serialize(self, out_dict: dict):
        pass

    def on_deserialize(self, in_dict: dict):
        pass

    @property
    def game(self):
        return self._node.game

    @property
    def node(self):
        return self._node

    @property
    def parent(self):
        return self._node.parent

    @property
    def transform(self):
        return self._node.transform

    @property
    def receive_updates(self):
        return self._receive_updates

    @receive_updates.setter
    def receive_updates(self, rcv: bool):
        self._receive_updates = rcv

        if not self.node.game:
            return

        if rcv:
            self.node.game.simulation.add_updatable(self)
        else:
            self.node.game.simulation.remove_updatable(self)

    @property
    def render_layer(self):
        return self._render_layer

    @render_layer.setter
    def render_layer(self, layer: int):
        if self.node.game is not None:
            self.node.game.simulation.remove_renderable(self, self._render_layer)
            self.node.game.simulation.add_renderable(self, layer)
        self._render_layer = layer

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, vis: bool):
        self._visible = vis

        if not self.node.game:
            return

        if vis:
            self.node.game.simulation.add_renderable(self, self.render_layer)
        else:
            self.node.game.simulation.remove_renderable(self, self.render_layer)
