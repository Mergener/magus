from common.binary import ByteReader, ByteWriter
from common.enums import DeliveryMode
from common.packet import Packet

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

        
def test_packet_encoding():
    original_packet = CustomPacket1(256, "Something", 800)
    writer = ByteWriter()
    original_packet.encode(writer)
    reader = ByteReader(writer.data)
    new_packet: CustomPacket1 = Packet.decode(reader)
    
    assert new_packet.int_value1 == original_packet.int_value1
    assert new_packet.str_value == original_packet.str_value
    assert new_packet.int_value2 == original_packet.int_value2