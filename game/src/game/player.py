from common.behaviours.network_behaviour import NetworkBehaviour, entity_packet_handler
from game.lobby import PlayerJoined


class Player(NetworkBehaviour):
    def on_init(self):
        self.index: int = 0
        self._local_player: bool = False

    def local_player(self):
        return self._local_player

    @entity_packet_handler(PlayerJoined)
    def _handle_player_joined(self, packet: PlayerJoined):
        self.index = packet.index
        self._local_player = packet.you
