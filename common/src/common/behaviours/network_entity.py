from __future__ import annotations

import asyncio
from abc import ABC
from typing import TYPE_CHECKING, Any, Callable, cast

import pygame as pg

from common.behaviour import Behaviour
from common.binary import ByteReader, ByteWriter
from common.network import DeliveryMode, Packet

if TYPE_CHECKING:
    from common.behaviours.network_entity_manager import NetworkEntityManager


class _PacketListenerState:
    def __init__(self, listener: Callable[[EntityPacket], Any]):
        self.listener = listener
        self.last_received_tick = 0


class NetworkEntity(Behaviour):
    _entity_manager: NetworkEntityManager

    def on_init(self):
        self._id: int = -1
        self._last_recv_pos = pg.Vector2(0, 0)
        self._prev_sent_pos = pg.Vector2(0, 0)
        self._approx_speed = pg.Vector2(0, 0)
        self._last_updated_tick = 0
        self._packet_listeners: dict[type[EntityPacket], list[_PacketListenerState]] = (
            {}
        )
        self._reached = True

    @property
    def id(self):
        return self._id

    @property
    def entity_manager(self):
        return self._entity_manager

    def on_pre_start(self):
        assert self.game

        if self.game.network.is_client():
            self.listen(PositionUpdate, lambda msg: self._handle_pos_update(msg))
            self.listen(RotationUpdate, lambda msg: self._handle_rotation_update(msg))
            self.listen(ScaleUpdate, lambda msg: self._handle_scale_update(msg))

    def _handle_rotation_update(self, packet: RotationUpdate):
        self.transform.rotation = packet.rotation

    def _handle_scale_update(self, packet: ScaleUpdate):
        self.transform.local_scale = pg.Vector2(packet.x, packet.y)

    def _handle_pos_update(self, packet: PositionUpdate):
        assert self.game

        if packet.tick_id < self._last_updated_tick:
            return

        # We want to deal with two different scenarios here, and
        # the system needs to be a little bit smart to decide which
        # of the two we're in right now.
        #
        # Scenario 1: The entity is moving. Here, we want to estimate
        # the speed and predict the motion in the client-side.
        #
        # Scenario 2: The entity is being teleported. The position update
        # in this case must be instant.
        #
        # When we receive a packet out of the blue, it is impossible to decide
        # on 1 or 2. However, if we've been receiving continuous packets in recent
        # ticks, we can assume it's scenario 1. For this reason, we'll
        # use this rule to decide on one vs the other.

        new_pos = pg.Vector2(packet.x, packet.y)
        time_diff = (
            packet.tick_id - self._last_updated_tick
        ) / self.game.simulation.tick_rate

        self._last_updated_tick = packet.tick_id

        if time_diff < 0.3:
            # Scenario 1: we're moving.
            space_diff = new_pos - self._last_recv_pos
            self._approx_speed = space_diff / time_diff
            self._reached = False
        else:
            # Scenario 2: teleporting
            self._approx_speed = pg.Vector2(0, 0)
            self._reached = True
            self.transform.position = new_pos

        self._last_recv_pos = new_pos

    def on_tick(self, tick_id: int) -> Any:
        assert self.game
        if self.game.network.is_server():
            pos = self.transform.position
            if self._prev_sent_pos != pos:
                self._prev_sent_pos = pos
                self.game.network.publish(
                    PositionUpdate(tick_id, self.id, pos.x, pos.y)
                )

    def on_update(self, dt: float):
        assert self.game

        if self.game.network.is_client():
            if self._reached:
                return

            pos = self.transform.position
            new_pos = pos + self._approx_speed * dt
            if (self._last_recv_pos - pos).length_squared() > (
                self._last_recv_pos - new_pos
            ).length_squared():
                self.transform.position = new_pos
            else:
                self.transform.position = self._last_recv_pos
                self._reached = True

    def _handle_entity_packet(self, packet: EntityPacket):
        handlers = self._packet_listeners.get(packet.__class__)
        if handlers is None:
            return

        for h in handlers:
            if packet.tick_id is not None:
                if h.last_received_tick > packet.tick_id:
                    continue
                h.last_received_tick = packet.tick_id

            res = h.listener(packet)
            if asyncio.iscoroutine(res):
                asyncio.create_task(res)

    def listen[T: EntityPacket](
        self, packet_type: type[T], listener: Callable[[T], None]
    ):
        listeners = self._packet_listeners.get(packet_type)
        if listeners is None:
            listeners = []
            self._packet_listeners[packet_type] = listeners
        listeners.append(
            _PacketListenerState(cast(Callable[[EntityPacket], None], listener))
        )

    def on_destroy(self):
        assert self.game
        self._packet_listeners.clear()


class EntityPacket(Packet, ABC):
    def __init__(self, id: int, tick_id: int | None = None):
        self.id = id
        self.tick_id = tick_id

    def on_write(self, writer: ByteWriter):
        if self.tick_id is not None:
            writer.write_int32(-self.id)
            writer.write_uint32(self.tick_id)
        else:
            writer.write_int32(self.id)

    def on_read(self, reader: ByteReader):
        self.id = reader.read_int32()
        if self.id < 0:
            self.id = -self.id
            self.tick_id = reader.read_uint32()
        else:
            self.tick_id = None


class PositionUpdate(EntityPacket):
    tick_id: int

    def __init__(self, tick_id: int, id: int, x: float, y: float):
        super().__init__(id, tick_id)
        self.tick_id = tick_id
        self.x = x
        self.y = y

    def on_write(self, writer: ByteWriter):
        super().on_write(writer)
        writer.write_uint32(self.tick_id)
        writer.write_float32(self.x)
        writer.write_float32(self.y)

    def on_read(self, reader: ByteReader):
        super().on_read(reader)
        self.tick_id = reader.read_uint32()
        self.x = reader.read_float32()
        self.y = reader.read_float32()

    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.UNRELIABLE


class ScaleUpdate(EntityPacket):
    tick_id: int

    def __init__(self, tick_id: int, id: int, x: float, y: float):
        super().__init__(id, tick_id)
        self.tick_id = tick_id
        self.x = x
        self.y = y

    def on_write(self, writer: ByteWriter):
        super().on_write(writer)
        writer.write_uint32(self.tick_id)
        writer.write_float32(self.x)
        writer.write_float32(self.y)

    def on_read(self, reader: ByteReader):
        super().on_read(reader)
        self.tick_id = reader.read_uint32()
        self.x = reader.read_float32()
        self.y = reader.read_float32()

    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.RELIABLE


class RotationUpdate(EntityPacket):
    tick_id: int

    def __init__(self, tick_id: int, id: int, rot: float):
        super().__init__(id, tick_id)
        self.tick_id = tick_id
        self.rotation = rot

    def on_write(self, writer: ByteWriter):
        super().on_write(writer)
        writer.write_uint32(self.tick_id)
        writer.write_float32(self.rotation)

    def on_read(self, reader: ByteReader):
        super().on_read(reader)
        self.tick_id = reader.read_uint32()
        self.rotation = reader.read_float32()

    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.RELIABLE
