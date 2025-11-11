from abc import ABC

from common.engine.binary import ByteReader, ByteWriter
from common.engine.enums import DeliveryMode
from common.engine.network import Packet


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
    def __init__(self, id: int, parent_id: int | None = None):
        self.id = id
        self.parent_id = parent_id

    def on_write(self, writer: ByteWriter):
        if self.parent_id:
            writer.write_int32(-self.id)
            writer.write_int32(self.parent_id)

    def on_read(self, reader: ByteReader):
        self.id = reader.read_int32()
        if self.id < 0:
            self.id = -self.id
            self.parent_id = reader.read_int32()

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
