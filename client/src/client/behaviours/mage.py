from client.behaviours.network_behaviour import NetworkBehaviour
from common.packets import EntityPacket


class Mage(NetworkBehaviour):
    def handle_packet(self, packet: EntityPacket):
        pass
