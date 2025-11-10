from abc import ABC
from typing import TYPE_CHECKING

from common.node import Node


class Behaviour(ABC):
    def __init__(self, node: Node):
        self._receive_updates: bool = True
        self._visible: bool = True
        self._render_layer: int = 0
        self._set_node(node)
        self.on_init()

    def on_init(self):
        """Called upon behaviour construction."""
        pass

    def on_start(self):
        """Called as soon as the behaviour is materialized in a simulation."""
        pass

    def on_update(self, dt: float):
        """Called every simulation frame, with variable interval."""
        pass

    def on_tick(self, tick_id: int):
        """Called every simulation tick, with fixed interval."""
        pass

    def on_destroy(self):
        """Called when this behaviour or its corresponding node gets destroyed."""
        pass

    def on_render(self):
        """Called every simulation render cycle."""
        pass

    @property
    def node(self):
        return self._node

    def _set_node(self, node: Node):
        if hasattr(self, "_node") and self.node != None and self.node.game:
            self.node.game.simulation.remove_renderable(self, self.render_layer)
            self.node.game.simulation.remove_tickable(self)
            self.node.game.simulation.remove_updatable(self)

        self._node = node

        # Setting properties so that setters are invoked.
        self.visible = self.visible
        self.receive_updates = self.receive_updates

        self.on_start()

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
        if self.node.game is None:
            return

        if rcv:
            self.node.game.simulation.add_tickable(self)
            self.node.game.simulation.add_updatable(self)
        else:
            self.node.game.simulation.remove_updatable(self)
            self.node.game.simulation.remove_tickable(self)

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
        if self.node.game is None:
            return

        if vis:
            self.node.game.simulation.add_renderable(self, self._render_layer)
        else:
            self.node.game.simulation.remove_renderable(self, self._render_layer)
