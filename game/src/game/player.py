from common.behaviours.network_behaviour import NetworkBehaviour, entity_packet_handler
from common.network import NetPeer
from game.lobby import PlayerJoined


class Player(NetworkBehaviour):
    def on_init(self):
        self.index: int = 0
        self._local_player: bool = False
        self._net_peer: NetPeer | None = None

    @property
    def net_peer(self):
        """
        Server-only.
        The peer associated with this player.
        """
        return self._net_peer

    def local_player(self):
        return self._local_player

    @entity_packet_handler(PlayerJoined)
    def _handle_player_joined(self, packet: PlayerJoined):
        self.index = packet.index
        self._local_player = packet.you
