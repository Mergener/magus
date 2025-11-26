from typing import Collection

import enet

from common.binary import ByteReader, ByteWriter
from common.network import DeliveryMode, NetPeer, Network, Packet


class NetServer(Network):
    def __init__(
        self, address: str = "127.0.0.1", port: int = 9999, max_clients: int = 32
    ):
        super().__init__()
        self._address = enet.Address(address.encode("utf-8"), port)
        self._host = enet.Host(self._address, 128, 0, 0, 0)
        self._peers: dict[tuple[str, int], NetPeer] = {}
        print(f"Listening at port {port}")

    def publish(
        self,
        packet: Packet,
        override_delivery_mode: DeliveryMode | None = None,
        exclude_peers: list[NetPeer] | None = None,
    ):
        writer = ByteWriter()
        packet.encode(writer)
        mode = override_delivery_mode or packet.delivery_mode
        data = writer.data

        for net_peer in self._peers.values():
            if exclude_peers is not None and net_peer in exclude_peers:
                continue

            net_peer.send_raw(data, mode)

    def poll(self):
        while True:
            net_peer: NetPeer | None
            event = self._host.service(0)
            if event.type == enet.EVENT_TYPE_NONE:
                break

            if event.type == enet.EVENT_TYPE_CONNECT:
                net_peer = NetPeer(event.peer)
                self._peers[net_peer.address] = net_peer
                self.notify_connection(net_peer)
                print(f"New connection: {net_peer.address}")

            elif event.type == enet.EVENT_TYPE_RECEIVE:
                net_peer = self._peers.get(
                    (event.peer.address.host, event.peer.address.port)
                )
                if net_peer:
                    data = bytes(event.packet.data)
                    reader = ByteReader(data)
                    packet = Packet.decode(reader)
                    print(f"Received {packet}")
                    self.notify(packet, net_peer)

            elif event.type == enet.EVENT_TYPE_DISCONNECT:
                address = (event.peer.address.host, event.peer.address.port)
                disconnected = self._peers.pop(address)
                self.notify_disconnection(disconnected)
                print(f"Lost connection: {address}")

    def disconnect(self):
        for p in self._peers.values():
            p.disconnect()
        self._peers = {}
        self._host.destroy()

    def is_server(self) -> bool:
        return True

    def is_client(self) -> bool:
        return False

    @property
    def connected_peers(self) -> Collection[NetPeer]:
        return self._peers.values()
