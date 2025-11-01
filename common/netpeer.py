import enet

from common.enums import DeliveryMode

class NetPeer:
    def __init__(self, enet_peer):
        self._enet_peer = enet_peer
        self._host = self._enet_peer.address.host
        self._port = self._enet_peer.address.port

    def send(self, data: bytes, mode: DeliveryMode):
        channel, flags = mode.to_enet()
        packet = enet.Packet(data, flags)
        self._enet_peer.send(channel, packet)

    def disconnect(self):
        self._enet_peer.disconnect()
        
    @property
    def address(self) -> tuple[str, int]:
        return (self._host, self._port)