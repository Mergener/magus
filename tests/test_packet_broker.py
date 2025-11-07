from unittest.mock import Mock

from common.network import NetPeer, Packet, PacketBroker


class DummyPacket(Packet):
    def __init__(self, data=None):
        self.data = data

    def on_write(self, writer):
        pass

    def on_read(self, reader):
        pass

    @property
    def delivery_mode(self):
        return Mock()


class AnotherPacket(Packet):
    def on_write(self, writer):
        pass

    def on_read(self, reader):
        pass

    @property
    def delivery_mode(self):
        return Mock()


def test_add_and_dispatch_calls_listener():
    broker = PacketBroker()
    packet = DummyPacket("data")
    peer = Mock(spec=NetPeer)

    listener = Mock()

    broker.add_listener(DummyPacket, listener)
    broker.dispatch(packet, peer)

    listener.assert_called_once_with(packet, peer)


def test_dispatch_multiple_listeners_all_called():
    broker = PacketBroker()
    packet = DummyPacket()
    peer = Mock(spec=NetPeer)

    listener1 = Mock()
    listener2 = Mock()

    broker.add_listener(DummyPacket, listener1)
    broker.add_listener(DummyPacket, listener2)

    broker.dispatch(packet, peer)

    listener1.assert_called_once_with(packet, peer)
    listener2.assert_called_once_with(packet, peer)


def test_remove_listener_stops_calls():
    broker = PacketBroker()
    packet = DummyPacket()
    peer = Mock(spec=NetPeer)

    listener = Mock()
    broker.add_listener(DummyPacket, listener)
    broker.remove_listener(DummyPacket, listener)

    broker.dispatch(packet, peer)
    listener.assert_not_called()


def test_remove_listener_removes_key_when_last():
    broker = PacketBroker()
    listener = Mock()

    broker.add_listener(DummyPacket, listener)
    assert DummyPacket in broker._listeners

    broker.remove_listener(DummyPacket, listener)
    assert DummyPacket not in broker._listeners


def test_listeners_are_type_specific():
    broker = PacketBroker()
    dummy_listener = Mock()
    another_listener = Mock()

    broker.add_listener(DummyPacket, dummy_listener)
    broker.add_listener(AnotherPacket, another_listener)

    dummy_packet = DummyPacket()
    another_packet = AnotherPacket()
    peer = Mock(spec=NetPeer)

    broker.dispatch(dummy_packet, peer)
    dummy_listener.assert_called_once_with(dummy_packet, peer)
    another_listener.assert_not_called()

    broker.dispatch(another_packet, peer)
    another_listener.assert_called_once_with(another_packet, peer)


def test_dispatch_with_no_listeners_does_nothing():
    broker = PacketBroker()
    packet = DummyPacket()
    peer = Mock(spec=NetPeer)

    # Should not raise.
    broker.dispatch(packet, peer)
