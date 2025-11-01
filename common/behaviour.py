from abc import ABC

class Behaviour(ABC):
    def __init__(self, node: "Node"):
        self._node = node
        self._receive_updates = True
        self._visible = True
    
    @property
    def node(self):
        return self._node
    
    @property
    def simulation(self):
        return self._node.simulation
    
    @property
    def receive_updates(self):
        return self._receive_updates
    
    @receive_updates.setter
    def receive_updates(self, rcv: bool):
        self._receive_updates = rcv
        if self.simulation == None:
            return
        
        if rcv:
            self.simulation.add_tickable(self)
            self.simulation.add_updatable(self)
        else:
            self.simulation.remove_updatable(self)
            self.simulation.remove_tickable(self)
            
    @property
    def visible(self):
        return self._visible
    
    @visible.setter
    def visible(self, vis: bool):
        self._visible = vis
        if self.simulation == None:
            return
        
        if vis:
            self.simulation.add_renderable(self)
        else:
            self.simulation.remove_renderable(self)
    
    def on_start(self):
        pass
    
    def on_update(self, dt: float):
        pass
    
    def on_tick(self, tick_id: int):
        pass
    
    def on_destroy(self):
        pass
    
    def on_render(self):
        pass
    
