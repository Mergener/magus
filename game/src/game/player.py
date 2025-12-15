from __future__ import annotations

from typing import TYPE_CHECKING

from common.behaviours.network_behaviour import NetworkBehaviour, entity_packet_handler
from common.network import NetPeer
from common.utils import notnull
from game.lobby_base import PlayerJoined

if TYPE_CHECKING:
    from game.game_manager import GameManager
    from game.mage import Mage


class Player(NetworkBehaviour):
    def on_init(self):
        self._net_peer: NetPeer | None = None
        self._game_manager: GameManager | None = None
        self._mage: Mage | None = None
        self._index = self.use_sync_var(int, 0)
        self._local_player: bool = False
        self.player_name = self.use_sync_var(str, "Unnamed Player")
        self.coins = self.use_sync_var(int, 0)
        self.kills = self.use_sync_var(int, 0)
        self.deaths = self.use_sync_var(int, 0)
        self.team = self.use_sync_var(int, 0)
        self.wins = self.use_sync_var(int, 0)
        self.mage_entity_id = self.use_sync_var(int, -1)

    def is_local_player(self):
        return self._local_player

    @property
    def mage(self) -> Mage | None:
        from game.mage import Mage

        if self.game is None:
            return None

        if self._mage is None:
            if self.mage_entity_id != -1:
                entity = self.net_entity.entity_manager.get_entity_by_id(
                    self.mage_entity_id.value
                )
                if entity is not None:
                    mage = entity.node.get_behaviour(Mage)
                    if mage is not None:
                        self._mage = mage
                        return mage

            mages = self.game.scene.find_behaviours_in_children(Mage)
            for mage in mages:
                if mage.owner_index == self.index:
                    self._mage = mage
                    return mage

        return self._mage

    @property
    def index(self):
        return self._index.value

    @index.setter
    def index(self, value):
        self._index.value = value

    @property
    def net_peer(self):
        """
        Server-only.
        The peer associated with this player.
        """
        return self._net_peer

    @entity_packet_handler(PlayerJoined)
    def _handle_player_joined(self, packet: PlayerJoined, peer: NetPeer):
        self.index = packet.index

    def is_ally_of(self, player: Player):
        return self.team == player.team

    def is_enemy_of(self, player: Player):
        return self.team != player.team
