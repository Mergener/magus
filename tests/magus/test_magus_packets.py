from typing import cast

from common.engine.binary import ByteReader, ByteWriter
from common.engine.network import Packet, register_packets
from common.magus.entity_type import EntityType
from common.magus.packets import CreateEntity


def test_packets_simmetry():
    packets = [CreateEntity(0, EntityType.MAGE)]

    register_packets([packet.__class__ for packet in packets])

    for packet in packets:
        writer = ByteWriter()
        packet.encode(writer)

        reader = ByteReader(writer.data)
        decoded = Packet.decode(reader)
        for (
            k,
            v,
        ) in decoded.__dict__.items():
            assert v == packet.__dict__[k]
