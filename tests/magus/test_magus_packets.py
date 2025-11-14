from typing import cast

from common.binary import ByteReader, ByteWriter
from common.network import Packet, register_packets
from game.entity_type import EntityType
from game.packets import CreateEntity


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
