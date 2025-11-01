import enet
from common.enums import DeliveryMode
from common.netpeer import NetPeer

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

            if event.type == enet.EVENT_TYPE_CONNECT:
                net_peer = NetPeer(event.peer)
                self._peers[net_peer.address] = net_peer
                print(f"New connection: {net_peer.address}")

            elif event.type == enet.EVENT_TYPE_RECEIVE:
                net_peer = self._peers.get(net_peer.address)
                if net_peer:
                    data = bytes(event.packet.data)
                    received_messages.append((data, net_peer))
                    print(f"From {net_peer.address}: {data.decode()}")

            elif event.type == enet.EVENT_TYPE_DISCONNECT:
                net_peer = self._peers.pop(net_peer.address, None)
                print(f"Lost connection: {net_peer.address}")

        return received_messages
