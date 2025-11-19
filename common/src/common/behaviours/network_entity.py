import pygame as pg

from common.behaviours.network_behaviour import NetworkBehaviour
from common.packets import PositionUpdate


class NetworkEntity(NetworkBehaviour):
    def on_init(self):
        self._id: int = -1
        self._prev_pos = pg.Vector2(0, 0)
        self._approx_speed = pg.Vector2(0, 0)
        self._last_updated_tick = 0

    @property
    def id(self):
        return self._id

    def on_start(self):
        assert self.game
        self._position_listener = self.game.network.listen(
            PositionUpdate, lambda p, _: self.on_position_update(p)
        )

    def on_position_update(self, packet: PositionUpdate):
        assert self.game

        if packet.tick_id < self._last_updated_tick:
            return

        new_pos = pg.Vector2(packet.x, packet.y)
        time_diff = (
            packet.tick_id - self._last_updated_tick
        ) / self.game.simulation.tick_rate
        space_diff = new_pos - self._prev_pos
        self._approx_speed = space_diff / time_diff
        self._last_updated_tick = packet.tick_id
        self._prev_pos = new_pos

    def on_update(self, dt: float):
        curr_local_pos = self.transform.local_position
        self.transform.local_position = curr_local_pos + self._approx_speed * dt

    def on_destroy(self):
        assert self.game
        self.game.network.unlisten(PositionUpdate, self._position_listener)
