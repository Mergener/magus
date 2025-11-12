from typing import cast

from common.engine.binary import ByteReader, ByteWriter
from common.engine.network import DeliveryMode, Packet, register_packets


class CustomPacket1(Packet):
    def __init__(self, int_value1: int, str_value: str, int_value2: int):
        self.int_value1 = int_value1
        self.str_value = str_value
        self.int_value2 = int_value2

    def on_write(self, writer: ByteWriter):
        writer.write_int32(self.int_value1)
        writer.write_str(self.str_value)
        writer.write_int64(self.int_value2)

    def on_read(self, reader: ByteReader):
        self.int_value1 = reader.read_int32()
        self.str_value = reader.read_str()
        self.int_value2 = reader.read_int64()

    @property
    def delivery_mode(self):
        return DeliveryMode.RELIABLE


class CustomPacket2(Packet):
    def __init__(self, foo: str, bar: str, baz: int):
        self.foo = foo
        self.bar = bar
        self.baz = baz

    def on_write(self, writer: ByteWriter):
        writer.write_str(self.foo)
        writer.write_str(self.bar)
        writer.write_uint64(self.baz)

    def on_read(self, reader: ByteReader):
        self.foo = reader.read_str()
        self.bar = reader.read_str()
        self.baz = reader.read_uint64()

    @property
    def delivery_mode(self):
        return DeliveryMode.RELIABLE_ORDERED


def test_packet_encoding():
    register_packets([CustomPacket1, CustomPacket2])
    original_packet1 = CustomPacket1(256, "Something", 800)
    writer = ByteWriter()
    original_packet1.encode(writer)
    reader = ByteReader(writer.data)
    new_packet1 = cast(CustomPacket1, Packet.decode(reader))

    assert new_packet1.int_value1 == original_packet1.int_value1
    assert new_packet1.str_value == original_packet1.str_value
    assert new_packet1.int_value2 == original_packet1.int_value2

    original_packet2 = CustomPacket2("Somefoo", "somebar", 8000000)
    writer = ByteWriter()
    original_packet2.encode(writer)
    reader = ByteReader(writer.data)
    new_packet2 = cast(CustomPacket2, Packet.decode(reader))

    assert new_packet2.foo == original_packet2.foo
    assert new_packet2.bar == original_packet2.bar
    assert new_packet2.baz == original_packet2.baz
