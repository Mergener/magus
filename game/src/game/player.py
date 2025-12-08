from typing import TYPE_CHECKING

from common.behaviours.network_behaviour import NetworkBehaviour, entity_packet_handler
from common.network import NetPeer
from common.utils import notnull
from game.lobby import PlayerJoined

if TYPE_CHECKING:
    from game.game_manager import GameManager
    from game.mage import Mage


class Player(NetworkBehaviour):
    def on_init(self):
        self.index: int = 0
        self._local_player: bool = False
        self._net_peer: NetPeer | None = None
        self._game_manager: GameManager | None = None
        self.mage: Mage | None = None
        self.coins = self.use_sync_var(int, 0)
        self.kills = self.use_sync_var(int, 0)
        self.deaths = self.use_sync_var(int, 0)

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
    def _handle_player_joined(self, packet: PlayerJoined, peer: NetPeer):
        self.index = packet.index
        self._local_player = packet.you
