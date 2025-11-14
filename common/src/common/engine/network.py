import traceback
from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum
from sys import stderr
from typing import Callable, cast

import enet

from common.engine.binary import ByteReader, ByteWriter


class DeliveryMode(Enum):
    UNRELIABLE = 0
    RELIABLE = 1
    RELIABLE_ORDERED = 2

    def to_enet(self) -> tuple[int, int]:
        """
        Returns (channel_id, enet_flags) for sending packets.
        """
        if self is DeliveryMode.UNRELIABLE:
            return 1, enet.PACKET_FLAG_UNSEQUENCED
        if self is DeliveryMode.RELIABLE:
            return 1, enet.PACKET_FLAG_RELIABLE
        if self is DeliveryMode.RELIABLE_ORDERED:
            return 0, enet.PACKET_FLAG_RELIABLE
        raise ValueError(f"Unknown DeliveryMode: {self}")

    @classmethod
    def from_enet(cls, flags: int, channel: int) -> "DeliveryMode":
        """
        Detects the DeliveryMode from ENet flags and channel.
        - channel 0 + RELIABLE → RELIABLE_ORDERED
        - channel 1 + RELIABLE → RELIABLE
        - UNSEQUENCED → UNRELIABLE
        """
        if flags & enet.PACKET_FLAG_UNSEQUENCED:
            return cls.UNRELIABLE
        if flags & enet.PACKET_FLAG_RELIABLE:
            if channel == 0:
                return cls.RELIABLE_ORDERED
            else:
                return cls.RELIABLE
        return cls.UNRELIABLE


class Packet(ABC):
    @abstractmethod
    def on_write(self, writer: ByteWriter):
        pass

    @abstractmethod
    def on_read(self, reader: ByteReader):
        pass

    @property
    @abstractmethod
    def delivery_mode(self) -> DeliveryMode:
        pass

    @classmethod
    def decode(cls, reader: ByteReader):
        global _packet_types
        packet_id = reader.read_uint8()
        if packet_id > len(_packet_types) or packet_id < 0:
            return NullPacket()

        packet_type = _packet_types[packet_id]
        packet = packet_type.__new__(packet_type)
        packet.on_read(reader)
        return packet

    def encode(self, writer: ByteWriter):
        global _packet_ids
        packet_id = _packet_ids[self.__class__]
        writer.write_uint8(packet_id)
        self.on_write(writer)


class NullPacket(Packet):
    def on_write(self, writer: ByteWriter):
        pass

    def on_read(self, reader: ByteReader):
        pass

    @property
    def delivery_mode(self):
        return DeliveryMode.UNRELIABLE


class CombinedPacket(Packet):
    def __init__(
        self, packets: list[Packet], delivery_mode: DeliveryMode | None = None
    ):
        self.packets = packets
        self._delivery_mode: DeliveryMode | None = delivery_mode

    def on_write(self, writer: ByteWriter):
        writer.write_uint8(len(self.packets))
        for p in self.packets:
            p.encode(writer)

    def on_read(self, reader: ByteReader):
        n = reader.read_uint8()
        self.packets = [Packet.decode(reader) for _ in range(n)]

    @property
    def delivery_mode(self) -> DeliveryMode:
        if self._delivery_mode is not None:
            return self._delivery_mode

        most_reliable_mode = DeliveryMode.UNRELIABLE
        for p in self.packets:
            if p.delivery_mode.value > most_reliable_mode.value:
                most_reliable_mode = p.delivery_mode
        return most_reliable_mode


class NetPeer:
    def __init__(self, enet_peer):
        self._enet_peer = enet_peer
        self._host = self._enet_peer.address.host
        self._port = self._enet_peer.address.port

    def send_raw(self, data: bytes, mode: DeliveryMode):
        channel, flags = mode.to_enet()
        packet = enet.Packet(data, flags)
        self._enet_peer.send(channel, packet)

    def send(self, packet: Packet, override_mode: DeliveryMode | None = None):
        writer = ByteWriter()
        packet.encode(writer)
        mode = override_mode or packet.delivery_mode
        self.send_raw(writer.data, mode)

    def disconnect(self):
        self._enet_peer.disconnect()

    @property
    def address(self) -> tuple[str, int]:
        return (self._host, self._port)


class Network(ABC):
    def __init__(self):
        self._listener_id = 0
        self._listeners: defaultdict[type, list[Callable[[Packet, NetPeer], None]]] = (
            defaultdict(list)
        )

    @abstractmethod
    def is_server(self) -> bool:
        """Whether this is a server or not. Not necessarily equal to 'not is_client'"""
        pass

    @abstractmethod
    def is_client(self) -> bool:
        """Whether this is a client or not. Not necessarily equal to 'not is_server'"""
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def publish(
        self, packet: Packet, override_delivery_mode: DeliveryMode | None = None
    ):
        """
        Publishes a packet to all peers connected to this network.
        If this is the server, it will broadcast the packet to all clients.
        If this is a client, it will send the packet to the server only.
        """
        pass

    @abstractmethod
    def poll(self):
        """
        Polls the network for events. If packets have been received, listeners are expected to be
        properly notified here.
        """
        pass

    def notify(
        self,
        packet: Packet,
        source_peer: NetPeer,
        packet_type: type[Packet] | None = None,
    ):
        """
        Should only be called from a class that implements Network when a packet is received.
        Notifies listeners of the received packet.
        """
        assert packet_type is None or isinstance(packet, packet_type)
        packet_type = packet_type if packet_type is not None else type(packet)

        if packet_type == object:
            return

        listeners = self._listeners[packet_type]
        for l in listeners:
            try:
                if packet_type != CombinedPacket:
                    for p in packet_type.__bases__:
                        self.notify(packet, source_peer, p)

                    l(packet, source_peer)
                else:
                    for sub_packet in cast(CombinedPacket, packet).packets:
                        self.notify(sub_packet, source_peer)
            except Exception as e:
                error_stack_trace = traceback.format_exc()
                print(
                    f"Error during processing of packet of type {type(packet)}: {error_stack_trace}",
                    file=stderr,
                )

    def listen[T: Packet](self, t: type[T], listener: Callable[[T, NetPeer], None]):
        listener = cast(Callable[[Packet, NetPeer], None], listener)
        self._listeners[t].append(listener)
        return listener

    def unlisten[T: Packet](self, t: type[T], listener: Callable[[T, NetPeer], None]):
        l = self._listeners[t]
        l.remove(cast(Callable[[Packet, NetPeer], None], listener))
        if len(l) == 0:
            self._listeners.pop(t)


class NullNetwork(Network):
    def disconnect(self):
        pass

    def publish(
        self, packet: Packet, override_delivery_mode: DeliveryMode | None = None
    ):
        pass

    def poll(self):
        pass


_packet_types: list[type[Packet]] = []
_packet_ids: dict[type[Packet], int] = {}


def auto_resolve_packets():
    register_packets([c for c in Packet.__subclasses__()])  # type: ignore[type-abstract]


def register_packets(packets_to_register: list[type[Packet]]):
    global _packet_ids, _packet_types, _initialized

    _packet_types += packets_to_register  # type: ignore[type-abstract]
    _packet_types = list(set(_packet_types))
    _packet_types.sort(key=lambda c: f"{c.__module__}.{c.__name__}")
    _packet_ids = {}

    for i, c in enumerate(_packet_types):
        _packet_ids[c] = i
