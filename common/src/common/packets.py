from abc import ABC

from common.binary import ByteReader, ByteWriter
from common.network import DeliveryMode, Packet


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
