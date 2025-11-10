from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from common.behaviour import Behaviour
    from common.network import Network, NullNetwork
    from common.node import Node
    from common.simulation import Simulation


class Game:
    def __init__(
        self,
        simulation: Simulation | None = None,
        network: Network | None = None,
        scene: Node | None = None,
        global_object: Node | None = None,
    ):
        self._simulation = simulation or Simulation()
        self._network = network or NullNetwork()
        self._scene = scene or Node()
        self._global_object = global_object or Node()

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
