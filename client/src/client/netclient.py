import enet

from common.enums import DeliveryMode
from common.network import NetPeer, Network, Packet


class NetClient(Network):
    def __init__(self, address: str, port: int):
        super().__init__()
        self._host = enet.Host(None, 1, 2, 0, 0)
        self._peer: NetPeer | None = None
        self.connect(address, port)

    def connect(self, address: str, port: int):
        addr = enet.Address(address.encode("utf-8"), port)
        peer = self._host.connect(addr, 2, 0)
        event = self._host.service(5000)

        if event.type != enet.EVENT_TYPE_CONNECT:
            raise ConnectionError(f"Failed to connect to {address}:{port}")

        self._peer = NetPeer(peer)
        print(f"Connected to {address}:{port}")

    def publish(
        self, packet: Packet, override_delivery_mode: DeliveryMode | None = None
    ):
        if not self._peer:
            raise RuntimeError("Not connected to any host.")

        self._peer.send(packet, override_delivery_mode)
        print(self._peer.address)

    def poll(self):
        messages = []
        while True:
            event = self._host.service(0)
            if event.type == enet.EVENT_TYPE_NONE:
                break
            elif event.type == enet.EVENT_TYPE_RECEIVE:
                messages.append(bytes(event.packet.data))
            elif event.type == enet.EVENT_TYPE_DISCONNECT:
                print("Disconnected from server.")
                self._peer = None
                break
        return messages

    def disconnect(self):
        if self._peer is None:
            return

        self._peer.disconnect()
