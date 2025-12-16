from sys import stderr
from typing import Collection

import enet

from common.binary import ByteReader
from common.network import DeliveryMode, NetPeer, Network, Packet


class NetClient(Network):
    def __init__(self, address: str, port: int):
        super().__init__()
        self._host = enet.Host(None, 1, 2, 0, 0)
        self._peer: NetPeer | None = None
        self._address = address
        self._port = port

    def connect(self):
        address = self._address
        port = self._port
        addr = enet.Address(address.encode("utf-8"), port)
        peer = self._host.connect(addr, 2, 0)
        event = self._host.service(5000)

        if event.type != enet.EVENT_TYPE_CONNECT:
            raise ConnectionError(f"Failed to connect to {address}:{port}")

        self._peer = NetPeer(peer)
        print(f"Connected to {address}:{port}")

    def publish(
        self,
        packet: Packet,
        override_delivery_mode: DeliveryMode | None = None,
        exclude_peers: list[NetPeer] | None = None,
    ):
        if not self._peer:
            print("Not connected to any host.", file=stderr)
            return

        self._peer.send(packet, override_delivery_mode)

    def poll(self):
        while True:
            event = self._host.service(0)
            if event.type == enet.EVENT_TYPE_NONE:
                break
            elif event.type == enet.EVENT_TYPE_RECEIVE:
                raw_data, raw_peer = event.packet.data, event.peer

                if self._peer is None or raw_peer.address.host != self._peer.address[0]:
                    continue

                reader = ByteReader(raw_data)
                decoded = Packet.decode(reader)

                self.notify(decoded, self._peer)

            elif event.type == enet.EVENT_TYPE_DISCONNECT:
                print("Disconnected from server.")
                self._peer = None
                break

    def disconnect(self):
        if self._peer is None:
            return

        self._peer.disconnect()

    def is_server(self) -> bool:
        return False

    def is_client(self) -> bool:
        return True

    @property
    def connected_peers(self) -> Collection[NetPeer]:
        return [self._peer] if self._peer else []
