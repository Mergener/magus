from client.behaviours.network_behaviour import NetworkBehaviour
from common.packets import EntityPacket


class Mage(NetworkBehaviour):
    def handle_packet(self, packet: EntityPacket):
        pass

    def on_update(self, dt: float):
        assert self.parent
        # self.parent.transform.rotation += 20 * dt
        self.transform.rotation += 20 * dt
