import pygame as pg

from common.simulation import Behaviour

class Player(Behaviour):
    def __init__(self):
        super().__init__()
        
    def on_update(self, dt):
        keys = pg.key.get_pressed()  

        if keys[pg.K_w]:
            self.transform.position.y -= 200 * dt
        if keys[pg.K_s]:
            self.transform.position.y += 200 * dt
        if keys[pg.K_a]:
            self.transform.position.x -= 200 * dt
        if keys[pg.K_d]:
            self.transform.position.x += 200 * dt
            