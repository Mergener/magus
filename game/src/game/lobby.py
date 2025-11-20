from __future__ import annotations

from common.behaviours.network_entity import EntityPacket
from common.binary import ByteReader, ByteWriter
from common.network import DeliveryMode, Packet


class LobbyInfo:
    def __init__(self):
        self.name = "New Lobby"
        self.capacity = 10

    def update_from_packet(self, packet: UpdateLobbyInfo):
        if packet.name is not None:
            self.name = packet.name

        if packet.capacity is not None:
            self.capacity = max(1, min(255, packet.capacity))


class StartGameRequest(Packet):
    def on_write(self, writer: ByteWriter):
        pass

    def on_read(self, reader: ByteReader):
        pass

    @property
    def delivery_mode(self):
        return DeliveryMode.RELIABLE


class JoinGameRequest(Packet):
    def on_write(self, writer: ByteWriter):
        pass

    def on_read(self, reader: ByteReader):
        pass

    @property
    def delivery_mode(self):
        return DeliveryMode.RELIABLE


class JoinGameResponse(Packet):
    accepted: bool

    def __init__(self, accepted: bool):
        self.accepted = accepted

    def on_write(self, writer: ByteWriter):
        writer.write_bool(self.accepted)

    def on_read(self, reader: ByteReader):
        self.accepted = reader.read_bool()

    @property
    def delivery_mode(self):
        return DeliveryMode.RELIABLE_ORDERED


class PlayerJoined(EntityPacket):
    def __init__(self, entity_id: int, index: int, you: bool):
        super().__init__(entity_id, None)
        self.index = index
        self.you = you

    def on_write(self, writer: ByteWriter):
        super().on_write(writer)
        writer.write_uint8(self.index)
        writer.write_bool(self.you)

    def on_read(self, reader: ByteReader):
        super().on_read(reader)
        self.index = reader.read_uint8()
        self.you = reader.read_bool()

    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.RELIABLE_ORDERED


class UpdateLobbyInfo(Packet):
    def __init__(self, name: str | None, capacity: int | None):
        self.name = name
        self.capacity = capacity

    def on_write(self, writer: ByteWriter):
        if self.name:
            writer.write_bool(True)
            writer.write_str(self.name)
        else:
            writer.write_bool(False)

        if self.capacity:
            writer.write_bool(True)
            writer.write_uint8(self.capacity)
        else:
            writer.write_bool(False)

    def on_read(self, reader: ByteReader):
        if reader.read_bool():
            self.name = reader.read_str()

        if reader.read_bool():
            self.capacity = reader.read_uint8()

    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.RELIABLE_ORDERED
