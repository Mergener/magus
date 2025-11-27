from __future__ import annotations

import asyncio
from abc import ABC
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Generic, TypeVar, cast

import pygame as pg

from common.behaviour import Behaviour
from common.binary import ByteReader, ByteWriter
from common.network import DeliveryMode, NetPeer, Packet

if TYPE_CHECKING:
    from common.behaviours.network_entity_manager import NetworkEntityManager


class _PacketListenerState:
    def __init__(self, listener: Callable[[EntityPacket, NetPeer], Any]):
        self.listener = listener
        self.last_received_tick = 0


PlausibleSyncVarType = bool | int | float | str | pg.Vector2

TVar = TypeVar("TVar", bound=PlausibleSyncVarType)


@dataclass
class SyncVar(Generic[TVar]):
    _id: int
    _current_value: TVar
    _last_sent_value: TVar | None
    _last_recv_tick: int
    _delivery_mode: DeliveryMode

    @property
    def value(self):
        return self._current_value

    @value.setter
    def value(self, v):
        self._current_value = v


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
        self._sync_vars: list[SyncVar] = []
        self._reached = True
        self._next_sync_var_id = 0
        self._may_register_sync_vars = True

    @property
    def id(self):
        return self._id

    @property
    def entity_manager(self):
        return self._entity_manager

    def use_sync_var[T: PlausibleSyncVarType](
        self,
        t: type[T],
        initial_value: T | None = None,
        delivery_mode=DeliveryMode.RELIABLE,
    ):
        assert self._may_register_sync_vars

        if initial_value is None:
            initial_value = t()  # type: ignore

        sync_var = SyncVar(
            self._next_sync_var_id, initial_value, None, 0, delivery_mode  # type: ignore
        )
        self._next_sync_var_id += 1
        self._sync_vars.append(sync_var)
        return sync_var

    def on_pre_start(self):
        assert self.game

        if self.game.network.is_client():
            self.listen(
                PositionUpdate, lambda msg, peer: self._handle_pos_update(msg, peer)
            )
            self.listen(
                RotationUpdate,
                lambda msg, peer: self._handle_rotation_update(msg, peer),
            )
            self.listen(
                ScaleUpdate, lambda msg, peer: self._handle_scale_update(msg, peer)
            )
            self.listen(
                SyncVarUpdate, lambda msg, peer: self._handle_sync_var_update(msg, peer)
            )

    def on_start(self) -> Any:
        self._may_register_sync_vars = False

    def _handle_rotation_update(self, packet: RotationUpdate, peer: NetPeer):
        self.transform.rotation = packet.rotation

    def _handle_scale_update(self, packet: ScaleUpdate, peer: NetPeer):
        self.transform.local_scale = pg.Vector2(packet.x, packet.y)

    def _handle_pos_update(self, packet: PositionUpdate, peer: NetPeer):
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

    def _handle_sync_var_update(self, update: SyncVarUpdate, peer: NetPeer):
        for p in self._sync_vars:
            if p._id != update.sync_var_id:
                continue
            if p._last_recv_tick is not None and (
                update.tick_id is None or p._last_recv_tick >= update.tick_id
            ):
                continue

            p._current_value = update.value

            if self.game:
                p._last_recv_tick = self.game.simulation.tick_id
            else:
                p._last_recv_tick = 0
            break

    def on_tick(self, tick_id: int) -> Any:
        assert self.game
        if self.game.network.is_server():
            pos = self.transform.position
            if self._prev_sent_pos != pos:
                self._prev_sent_pos = pos
                self.game.network.publish(
                    PositionUpdate(tick_id, self.id, pos.x, pos.y)
                )

            for sv in self._sync_vars:
                if sv._current_value != sv._last_sent_value:
                    sv._last_sent_value = sv._current_value
                    self.game.network.publish(
                        SyncVarUpdate(
                            self.id,
                            tick_id,
                            sv._id,
                            sv._current_value,
                            sv._delivery_mode,
                        )
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

    def _handle_entity_packet(self, packet: EntityPacket, peer: NetPeer):
        handlers = self._packet_listeners.get(packet.__class__)
        if handlers is None:
            return

        for h in handlers:
            if packet.tick_id is not None:
                if h.last_received_tick > packet.tick_id:
                    continue
                h.last_received_tick = packet.tick_id

            res = h.listener(packet, peer)
            if asyncio.iscoroutine(res):
                asyncio.create_task(res)

    def listen[T: EntityPacket](
        self, packet_type: type[T], listener: Callable[[T, NetPeer], None]
    ):
        listeners = self._packet_listeners.get(packet_type)
        if listeners is None:
            listeners = []
            self._packet_listeners[packet_type] = listeners
        listeners.append(
            _PacketListenerState(cast(Callable[[EntityPacket, NetPeer], Any], listener))
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


_sync_var_writers: dict[
    type[PlausibleSyncVarType], Callable[[Any, ByteWriter], Any]
] = {
    bool: lambda x, writer: writer.write_bool(x),
    int: lambda x, writer: writer.write_int32(x),
    float: lambda x, writer: writer.write_float32(x),
    str: lambda x, writer: writer.write_str(x),
    pg.Vector2: lambda x, writer: (
        writer.write_float32(x.x),
        writer.write_float32(x.y),
    ),
}


_sync_var_readers: dict[type[PlausibleSyncVarType], Callable[[ByteReader], Any]] = {
    bool: lambda reader: reader.read_bool(),
    int: lambda reader: reader.read_int32(),
    float: lambda reader: reader.read_float32(),
    str: lambda reader: reader.read_str(),
    pg.Vector2: lambda reader: pg.Vector2(reader.read_float32(), reader.read_float32()),
}


_sync_var_type_ids = {bool: 0, int: 1, float: 2, str: 3, pg.Vector2: 4}


_sync_var_id_types = [bool, int, float, str, pg.Vector2]


class SyncVarUpdate(EntityPacket):

    def __init__(
        self,
        entity_id: int,
        tick_id: int,
        sync_var_id: int,
        value: PlausibleSyncVarType,
        delivery_mode: DeliveryMode,
    ):
        super().__init__(entity_id, tick_id)
        self.sync_var_id = sync_var_id
        self.value = value
        self._delivery_mode = delivery_mode

    def on_write(self, writer: ByteWriter):
        super().on_write(writer)
        writer.write_uint8(self.sync_var_id)

        t = type(self.value)
        writer.write_uint8(_sync_var_type_ids[t])

        _sync_var_writers[t](self.value, writer)

    def on_read(self, reader: ByteReader):
        super().on_read(reader)
        self.sync_var_id = reader.read_uint8()

        t = _sync_var_id_types[reader.read_uint8()]

        self.value = _sync_var_readers[t](reader)
        self._delivery_mode = DeliveryMode.RELIABLE

    @property
    def delivery_mode(self) -> DeliveryMode:
        return self._delivery_mode


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
