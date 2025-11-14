from client.behaviours.network_behaviour import NetworkBehaviour
from game.packets import EntityPacket


class Mage(NetworkBehaviour):
    def handle_packet(self, packet: EntityPacket):
        pass
