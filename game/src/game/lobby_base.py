from __future__ import annotations

from dataclasses import dataclass, field

from common.behaviours.network_entity import EntityPacket
from common.binary import ByteReader, ByteWriter
from common.network import DeliveryMode, Packet


@dataclass
class LobbyInfo:
    players: list[tuple[str, int, int]] = field(default_factory=list)
    name: str = field(default="New Lobby")
    capacity: int = field(default=10)

    def from_packet(self, packet: LobbyInfoPacket):
        self.name = packet.name
        self.capacity = max(1, min(255, packet.capacity))

    def to_packet(self, packet: LobbyInfoPacket):
        return LobbyInfoPacket(self.name, self.capacity, self.players)

    def from_update_packet(self, packet: UpdateLobbyRequest):
        if packet.name:
            self.name = packet.name

        if packet.capacity:
            self.capacity = packet.capacity


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


class GameStarting(Packet):
    def on_write(self, writer: ByteWriter):
        pass

    def on_read(self, reader: ByteReader):
        pass

    @property
    def delivery_mode(self):
        return DeliveryMode.RELIABLE_ORDERED


class DoneLoadingGameScene(Packet):
    def on_write(self, writer: ByteWriter):
        pass

    def on_read(self, reader: ByteReader):
        pass

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


class QuitLobby(Packet):
    def on_write(self, writer: ByteWriter):
        pass

    def on_read(self, reader: ByteReader):
        pass

    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.RELIABLE_ORDERED


class PlayerLeft(EntityPacket):
    def __init__(self, entity_id: int, index: int):
        super().__init__(entity_id, None)
        self.index = index

    def on_write(self, writer: ByteWriter):
        super().on_write(writer)
        writer.write_uint8(self.index)

    def on_read(self, reader: ByteReader):
        super().on_read(reader)
        self.index = reader.read_uint8()

    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.RELIABLE_ORDERED


class LobbyInfoPacket(Packet):
    def __init__(self, name: str, capacity: int, players: list[tuple[str, int, int]]):
        self.name = name
        self.capacity = capacity
        self.players = players

    def on_write(self, writer: ByteWriter):
        writer.write_str(self.name or "Unnamed Lobby")
        writer.write_uint8(self.capacity)
        writer.write_uint8(len(self.players))
        for p in self.players:
            name, index, team = p
            writer.write_str(name)
            writer.write_uint8(index)
            writer.write_uint8(team)

    def on_read(self, reader: ByteReader):
        self.name = reader.read_str()
        self.capacity = reader.read_uint8()
        n_players = reader.read_uint8()
        self.players = []
        for i in range(n_players):
            self.players.append(
                (reader.read_str(), reader.read_uint8(), reader.read_uint8())
            )

    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.RELIABLE_ORDERED


class RequestLobbyInfo(Packet):
    def on_write(self, writer: ByteWriter):
        pass

    def on_read(self, reader: ByteReader):
        pass

    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.RELIABLE_ORDERED


class UpdateLobbyRequest(Packet):
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
