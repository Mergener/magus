from common.behaviour import Behaviour
from common.utils import overrides_method

class Simulation:
    def __init__(self, tick_rate: float = 1 / 15):
        self.tick_rate = tick_rate
        self._tick_accum_time = 0
        self._tick_id = 0
        self._updatables: set[Behaviour] = set()
        self._tickables: set[Behaviour] = set()
        self._renderables: set[Behaviour] = set()
        
    @property
    def tick_id(self):
        return self._tick_id
        
    def add_updatable(self, b: Behaviour):
        if overrides_method(Behaviour, b, "on_update"):
            self._updatables.add(b)
        
    def add_tickable(self, b: Behaviour):
        if overrides_method(Behaviour, b, "on_tick"):
            self._tickables.add(b)
        
    def add_renderable(self, b: Behaviour):
        if overrides_method(Behaviour, b, "on_render"):
            self._renderables.add(b)
        
    def remove_updatable(self, b: Behaviour):
        self._updatables.discard(b)
        
    def remove_tickable(self, b: Behaviour):
        self._tickables.discard(b)
        
    def remove_renderable(self, b: Behaviour):
        self._renderables.discard(b)
        
    def update(self, dt):
        self._tick_accum_time += dt
        
        if self._tick_accum_time > self.tick_rate:
            self._tick_accum_time -= self.tick_rate
            for t in self._tickables:
                t.on_tick(self._tick_id)
            self._tick_id += 1
            
        for u in self._updatables:
            u.on_update(dt)
            
    def render(self):
        for r in self._renderables:
            r.on_render()
        
    