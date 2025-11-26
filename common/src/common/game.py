from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from common.network import Network, NullNetwork
    from common.node import Node
    from common.simulation import Simulation
    from common.behaviour import Behaviour
    from common.input import Input

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
        from common.input import Input
        from common.network import Network, NullNetwork
        from common.node import Node
        from common.simulation import Simulation

        self._simulation = simulation or Simulation()
        self._network: Network = network or NullNetwork()
        self._scene = scene or Node()
        self._global_object = global_object or Node()
        self._display = display
        self._started = False
        self._queued_scene: Node | None = None
        self._queued_nodes_to_transfer: list[Node] | None = None
        self._stopped = False
        self._input = Input()

    @property
    def stopped(self):
        return self._stopped

    def quit(self):
        self._stopped = True

    @property
    def simulation(self):
        return self._simulation

    @property
    def input(self):
        return self._input

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
        if self.stopped:
            return

        if not self._started:
            self._started = True
            self.global_object.bind_to_game(self)
            self.scene.bind_to_game(self)

        if self._queued_scene is not None:
            prev_scene = self._scene
            self._scene = self._queued_scene
            self._scene.bind_to_game(self)

            if self._queued_nodes_to_transfer is not None:
                for n in self._queued_nodes_to_transfer:
                    n.parent = self._scene

            prev_scene.destroy()
            self._queued_scene = None
            self._queued_nodes_to_transfer = None

        self.network.poll()
        self.simulation.iterate()

        if not self.headless:
            if (
                self._display is not None
            ):  # Condition always true, but needed for type checker
                self._display.fill("black")
            self.simulation.render()
            pg.display.update()

    def handle_pygame_events(self, events: list[pg.event.Event]):
        must_stop = self._input.handle_pygame_events(events)
        if must_stop:
            self.quit()

    def load_scene(self, node: Node, nodes_to_transfer: list[Node] | None = None):
        print(f"Loading new scene: {node.name}")
        self._queued_scene = node
        self._queued_nodes_to_transfer = nodes_to_transfer

    def cleanup(self):
        self.network.disconnect()


_null_game = Game()


def get_null_game():
    return _null_game
