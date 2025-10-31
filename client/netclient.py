import enet

from common.enums import DeliveryMode

class NetClient:
    def __init__(self, address: str, port: int):
        self._host = enet.Host(None, 1, 2, 0, 0)
        self._peer = None
        self.connect(address, port)

    def connect(self, address: str, port: int):
        addr = enet.Address(address.encode('utf-8'), port)
        self._peer = self._host.connect(addr, 2, 0)
        event = self._host.service(5000)
        
        if event.type != enet.EVENT_TYPE_CONNECT:
            raise ConnectionError(f"Failed to connect to {address}:{port}")
        
        print(f"Connected to {address}:{port}")

    def send(self, data: bytes, mode: DeliveryMode):
        if not self._peer:
            raise RuntimeError("Not connected to any host.")

        flags, channel = mode.to_enet()
        packet = enet.Packet(data, flags)
        self._peer.send(channel, packet)
        self._host.flush()

    def poll(self) -> list[bytes]:
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
