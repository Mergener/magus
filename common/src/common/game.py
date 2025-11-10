from __future__ import annotations

import traceback
from sys import stderr
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from common.network import Network, NullNetwork
    from common.node import Node
    from common.simulation import Simulation

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
        self._simulation = simulation or Simulation()
        self._network = network or NullNetwork()
        self._scene = scene or Node()
        self._global_object = global_object or Node()
        self._screen: pg.Surface | None = None
        self._display = display

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
    def screen(self):
        return self._screen

    @property
    def headless(self):
        return self._display is None

    def initialize(self):
        self.global_object.bind_to_game(self)
        self.scene.bind_to_game(self)

    def iterate(self):
        self.network.poll()
        self.simulation.iterate()

        if not self.headless:
            if (
                self._display is not None
            ):  # Condition always true, but needed for type checker
                self._display.fill("black")
            self.simulation.render()
            pg.display.update()

    def cleanup(self):
        self.network.disconnect()
