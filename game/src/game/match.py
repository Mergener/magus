from common.binary import ByteReader, ByteWriter
from common.network import DeliveryMode, Packet


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
