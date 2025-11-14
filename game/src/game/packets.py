from abc import ABC

from common.binary import ByteReader, ByteWriter
from common.network import DeliveryMode, Packet
from game.entity_type import EntityType


class NewGame(Packet):
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
    def on_write(self, writer: ByteWriter):
        pass

    def on_read(self, reader: ByteReader):
        pass

    @property
    def delivery_mode(self):
        return DeliveryMode.RELIABLE


class CreateEntity(Packet):
    def __init__(self, id: int, type_id: EntityType, parent_id: int | None = None):
        self.id = id
        self.parent_id = parent_id
        self.type_id = type_id

    def on_write(self, writer: ByteWriter):
        if self.parent_id:
            writer.write_int32(-self.id)
            writer.write_int32(self.parent_id)
        else:
            writer.write_int32(self.id)
        writer.write_uint8(self.type_id.value)

    def on_read(self, reader: ByteReader):
        self.id = reader.read_int32()
        if self.id < 0:
            self.id = -self.id
            self.parent_id = reader.read_int32()
        self.type_id = EntityType(reader.read_uint8())

    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.RELIABLE_ORDERED


class DestroyEntity(Packet):
    def __init__(self, id: int):
        self.id = id

    def on_write(self, writer: ByteWriter):
        writer.write_int32(self.id)

    def on_read(self, reader: ByteReader):
        self.id = reader.read_int32()

    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.RELIABLE_ORDERED


class EntityPacket(Packet, ABC):
    def __init__(self, id: int):
        self.id = id

    def on_write(self, writer: ByteWriter):
        writer.write_int32(self.id)

    def on_read(self, reader: ByteReader):
        self.id = reader.read_int32()


class PlayerJoined(Packet):
    def __init__(self, hero_entity: int, index: int):
        self.index = index
        self.hero_entity = hero_entity

    def on_write(self, writer: ByteWriter):
        writer.write_int32(self.hero_entity)
        writer.write_uint8(self.index)

    def on_read(self, reader: ByteReader):
        self.hero_entity = reader.read_int32()
        self.index = reader.read_uint8()

    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.RELIABLE_ORDERED


class PositionUpdate(EntityPacket):
    def __init__(self, tick_id: int, id: int, x: int, y: int):
        super().__init__(id)
        self.tick_id = tick_id
        self.x = x
        self.y = y

    def on_write(self, writer: ByteWriter):
        super().on_write(writer)
        writer.write_uint32(self.tick_id)
        writer.write_int32(self.x)
        writer.write_int32(self.y)

    def on_read(self, reader: ByteReader):
        super().on_read(reader)
        self.tick_id = reader.read_uint32()
        self.x = reader.read_int32()
        self.y = reader.read_int32()

    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.UNRELIABLE
