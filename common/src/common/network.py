from abc import ABC, abstractmethod
from collections import defaultdict
from sys import stderr
from typing import Callable, cast

import enet

from common.binary import ByteReader, ByteWriter
from common.enums import DeliveryMode


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
            print(f"Received invalid packet: {packet_id}", file=stderr)
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
        self._listeners: defaultdict[type, list[Callable[[Packet, NetPeer], None]]] = (
            defaultdict(list)
        )

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

    def notify(self, packet: Packet, source_peer: NetPeer):
        """
        Should only be called from a class that implements Network when a packet is received.
        Notifies listeners of the received packet.
        """
        for l in self._listeners[packet.__class__]:
            try:
                if not isinstance(packet, CombinedPacket):
                    l(packet, source_peer)
                else:
                    for p in packet.packets:
                        self.notify(p, source_peer)
            except Exception as e:
                print(f"Error during processing of packet of type {type(packet)}: {e}")

    def listen[T: Packet](self, t: type[T], listener: Callable[[T, NetPeer], None]):
        self._listeners[t].append(cast(Callable[[Packet, NetPeer], None], listener))

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
_initialized = False


def init_packets():
    global _packet_ids, _packet_types, _initialized

    if _initialized:
        return

    _initialized = True
    _packet_types = [c for c in Packet.__subclasses__()]  # type: ignore[type-abstract]
    _packet_types.sort(key=lambda c: f"{c.__module__}.{c.__name__}")

    for i, c in enumerate(_packet_types):
        _packet_ids[c] = i
