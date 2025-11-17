import pygame as pg

from common.behaviour import Behaviour
from common.behaviours.camera import Camera
from common.behaviours.network_behaviour import NetworkBehaviour


class Player(NetworkBehaviour):
    def on_update(self, dt):
        keys = pg.key.get_pressed()
        motion = pg.Vector2(0, 0)

        if keys[pg.K_w]:
            motion.y -= 1
        if keys[pg.K_s]:
            motion.y += 1
        if keys[pg.K_a]:
            motion.x -= 1
        if keys[pg.K_d]:
            motion.x += 1

        if motion.length_squared() != 0:
            self.transform.position += motion.normalize() * 200 * dt

        if keys[pg.K_UP] and Camera.main is not None:
            Camera.main.transform.position.y -= 250 * dt
        if keys[pg.K_DOWN] and Camera.main is not None:
            Camera.main.transform.position.y += 250 * dt
        if keys[pg.K_LEFT] and Camera.main is not None:
            Camera.main.transform.position.x -= 250 * dt
        if keys[pg.K_RIGHT] and Camera.main is not None:
            Camera.main.transform.position.x += 250 * dt
