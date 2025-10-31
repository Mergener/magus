from abc import ABC, abstractmethod
from typing import Type

from common.binary import ByteReader, ByteWriter
from common.enums import DeliveryMode

class Packet(ABC):
    @abstractmethod
    def on_write(self, writer: ByteWriter):
        pass
    
    @abstractmethod
    def on_read(self, reader: ByteReader):
        pass
    
    @property
    @abstractmethod
    def delivery_mode(self) -> DeliveryMode:
        pass
    
    @classmethod
    def decode(cls, reader: ByteReader):
        global _packet_types
        id = reader.read_uint8()
        packet_type = _packet_types[id]
        packet = packet_type.__new__(packet_type)
        packet.on_read(reader)
        return packet
    
    def encode(self, writer: ByteWriter):
        global _packet_ids
        id = _packet_ids[self.__class__]
        writer.write_uint8(id)
        self.on_write(writer)        

_packet_types: list[Type[Packet]] = []
_packet_ids: dict[Type[Packet], int] = {}

def init_packets():
    global _packet_ids, _packet_types
    _packet_types = [c for c in Packet.__subclasses__()]
    _packet_types.sort(key = lambda c: f"{c.__module__}.{c.__name__}")
    for i, c in enumerate(_packet_types):
        _packet_ids[c] = i