from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from common.engine.network import Network, NullNetwork
    from common.engine.node import Node
    from common.engine.simulation import Simulation

import pygame as pg


class Game:
    def __init__(
        self,
        display: pg.Surface | None = None,
        simulation: Simulation | None = None,
        network: Network | None = None,
        scene: Node | None = None,
        global_object: Node | None = None,
    ):
        from common.engine.network import Network, NullNetwork
        from common.engine.node import Node
        from common.engine.simulation import Simulation

        self._simulation = simulation or Simulation()
        self._network: Network = network or NullNetwork()
        self._scene = scene or Node()
        self._global_object = global_object or Node()
        self._display = display
        self._started = False

    @property
    def simulation(self):
        return self._simulation

    @property
    def network(self):
        return self._network

    @property
    def scene(self):
        return self._scene

    @property
    def global_object(self):
        return self._global_object

    @property
    def display(self):
        return self._display

    @property
    def headless(self):
        return self._display is None

    def iterate(self):
        if not self._started:
            self._started = True
            self.global_object.bind_to_game(self)
            self.scene.bind_to_game(self)

        self.network.poll()
        self.simulation.iterate()

        if not self.headless:
            if (
                self._display is not None
            ):  # Condition always true, but needed for type checker
                self._display.fill("black")
            self.simulation.render()
            pg.display.update()

    def load_scene(self, node: Node):
        self.scene.destroy()
        self._scene = node
        node.bind_to_game(self)

    def cleanup(self):
        self.network.disconnect()


_null_game = Game()


def get_null_game():
    return _null_game
