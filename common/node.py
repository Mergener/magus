from typing import Self

from common.behaviour import Behaviour
from common.simulation import Simulation

class Node:
    def __init__(self):
        self._behaviours: list["Behaviour"] = []
        self._children: list[Self] = []
        self._simulation: Simulation = None
        
    @property
    def simulation(self):
        return self._simulation
    
    @simulation.setter
    def simulation(self, simulation: Simulation):
        if self._simulation is not None:
            for b in self._behaviours:
                if b.receive_updates:
                    self._simulation.add_updatable(b)
                    self._simulation.add_tickable(b)
                    
                if b.visible:
                    self._simulation.add_renderable(b)
                
        self._simulation = simulation
        
        if simulation is not None:
            for b in self._behaviours:
                if b.receive_updates:
                    self._simulation.add_updatable(b)
                    self._simulation.add_tickable(b)
                    
                if b.visible:
                    self._simulation.add_renderable(b)
            