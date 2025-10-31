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

class NetServer:
    def __init__(self, address: str = "0.0.0.0", port: int = 9999, max_clients: int = 32):
        self._address = enet.Address(address.encode("utf-8"), port)
        self._host = enet.Host(self._address, max_clients, 2, 0, 0)
        self._peers: dict[tuple[str, int], NetPeer] = {}

    def broadcast(self, data: bytes, mode: DeliveryMode):
        for net_peer in self._peers.values():
            net_peer.send(data, mode)

    def poll(self) -> list[tuple[bytes, NetPeer]]:
        received_messages: list[tuple[bytes, NetPeer]] = []

        while True:
            event = self._host.service(0)
            if event.type == enet.EVENT_TYPE_NONE:
                break

            peer_key = (event.peer.address.host, event.peer.address.port)

            if event.type == enet.EVENT_TYPE_CONNECT:
                net_peer = NetPeer(event.peer)
                self._peers[peer_key] = net_peer
                print(f"New connection: {peer_key}")

            elif event.type == enet.EVENT_TYPE_RECEIVE:
                net_peer = self._peers.get(peer_key)
                if net_peer:
                    data = bytes(event.packet.data)
                    received_messages.append((data, net_peer))
                    print(f"From {peer_key}: {data.decode()}")

            elif event.type == enet.EVENT_TYPE_DISCONNECT:
                net_peer = self._peers.pop(peer_key, None)
                print(f"Lost connection: {peer_key}")

        return received_messages
