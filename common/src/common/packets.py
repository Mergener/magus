from abc import ABC
from typing import TYPE_CHECKING, cast

from common.binary import ByteReader, ByteWriter
from common.network import DeliveryMode, Packet

if TYPE_CHECKING:
    from common.behaviours.network_behaviour import SyncVarType


class EntityPacket(Packet, ABC):
    def __init__(self, id: int):
        self.id = id

    def on_write(self, writer: ByteWriter):
        writer.write_int32(self.id)

    def on_read(self, reader: ByteReader):
        self.id = reader.read_int32()


class PositionUpdate(EntityPacket):
    def __init__(self, tick_id: int, id: int, x: int, y: int):
        super().__init__(id)
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
        super().__init__(id)
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
        super().__init__(id)
        self.tick_id = tick_id
        self.rot = rot

    def on_write(self, writer: ByteWriter):
        super().on_write(writer)
        writer.write_uint32(self.tick_id)
        writer.write_float32(self.rot)

    def on_read(self, reader: ByteReader):
        super().on_read(reader)
        self.tick_id = reader.read_uint32()
        self.rot = reader.read_float32()

    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.RELIABLE


class SyncVarPacket(EntityPacket):
    write_var = [
        # Ordering based on SyncVarType enum on network_behaviour.py
        lambda x, writer: writer.write_int8(x),
        lambda x, writer: writer.write_int16(x),
        lambda x, writer: writer.write_int32(x),
        lambda x, writer: writer.write_int64(x),
        lambda x, writer: writer.write_uint8(x),
        lambda x, writer: writer.write_uint16(x),
        lambda x, writer: writer.write_uint32(x),
        lambda x, writer: writer.write_uint64(x),
        lambda x, writer: writer.write_float32(x),
        lambda x, writer: writer.write_float64(x),
        lambda x, writer: writer.write_str(x),
    ]
    read_var = [
        # Ordering based on SyncVarType enum on network_behaviour.py
        lambda reader: reader.read_int8(),
        lambda reader: reader.read_int16(),
        lambda reader: reader.read_int32(),
        lambda reader: reader.read_int64(),
        lambda reader: reader.read_uint8(),
        lambda reader: reader.read_uint16(),
        lambda reader: reader.read_uint32(),
        lambda reader: reader.read_uint64(),
        lambda reader: reader.read_float32(),
        lambda reader: reader.read_float64(),
        lambda reader: reader.read_str(),
    ]

    def __init__(
        self,
        entity_id: int,
        var_type: SyncVarType,
        value,
        tick_id: int,
        reliability: DeliveryMode = DeliveryMode.RELIABLE,
    ):
        super().__init__(entity_id)
        self.var_type = var_type
        self.reliability = reliability
        self.value = value

    def on_write(self, writer: ByteWriter):
        SyncVarPacket.write_var[cast(int, self.var_type.value)](self.value, writer)

    def on_read(self, reader: ByteReader):
        self.value = SyncVarPacket.read_var[cast(int, self.var_type.value)](reader)

    @property
    def delivery_mode(self) -> DeliveryMode:
        return self.reliability
