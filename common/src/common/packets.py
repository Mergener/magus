from abc import ABC
from typing import TYPE_CHECKING, cast

from common.binary import ByteReader, ByteWriter
from common.network import DeliveryMode, Packet
from game.entity_type import EntityType


class EntityPacket(Packet, ABC):
    def __init__(self, id: int, tick_id: int | None):
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


class CreateEntity(Packet):
    def __init__(self, id: int, type_id: int, parent_id: int | None = None):
        self.id = id
        self.parent_id = parent_id
        self.template_id = type_id

    def on_write(self, writer: ByteWriter):
        if self.parent_id:
            writer.write_int32(-self.id)
            writer.write_int32(self.parent_id)
        else:
            writer.write_int32(self.id)
        writer.write_uint8(self.template_id)

    def on_read(self, reader: ByteReader):
        self.id = reader.read_int32()
        if self.id < 0:
            self.id = -self.id
            self.parent_id = reader.read_int32()
        self.template_id = reader.read_uint8()

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
