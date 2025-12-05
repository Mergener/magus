import random
from typing import TYPE_CHECKING, Any

import pygame as pg

from common.behaviour import Behaviour
from common.behaviours.network_behaviour import NetworkBehaviour
from common.network import NetPeer
from common.primitives import Vector2
from common.utils import notnull
from game.lobby import LobbyInfo

if TYPE_CHECKING:
    from game.player import Player


class GameManager(NetworkBehaviour):
    def on_init(self) -> Any:
        self._players: list[Player] = []
        self._players_by_peer: dict[NetPeer, Player] = {}

    @property
    def players(self):
        return self._players

    def get_player_by_index(self, player_idx: int):
        if player_idx not in range(len(self._players)):
            return None
        return self._players[player_idx]

    def get_player_by_peer(self, peer: NetPeer):
        return self._players_by_peer[peer]

    def on_common_pre_start(self):
        for p in self.players:
            self._players_by_peer[notnull(p.net_peer)] = p

    def on_server_start(self):
        from game.mage import Mage

        for p in self.players:
            mage = self.entity_manager.spawn_entity("mage").node.get_or_add_behaviour(
                Mage
            )
            mage.owner_index.value = p.index
            mage.transform.position = Vector2(
                random.randint(-200, 200), random.randint(-200, 200)
            )
            p.mage = mage
            p._game_manager = self
