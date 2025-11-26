import random
from typing import TYPE_CHECKING, Any

import pygame as pg

from common.behaviour import Behaviour
from common.behaviours.network_behaviour import NetworkBehaviour
from game.lobby import LobbyInfo
from game.mage import Mage

if TYPE_CHECKING:
    from game.player import Player


class GameManager(NetworkBehaviour):
    def on_init(self) -> Any:
        self._players: list[Player] = []

    @property
    def players(self):
        return self._players

    def on_server_start(self):
        for p in self.players:
            mage = self.entity_manager.spawn_entity("mage").node.get_or_add_behaviour(
                Mage
            )
            mage.transform.position = pg.Vector2(
                random.randint(-200, 200), random.randint(-200, 200)
            )
            p.mage = mage
            p._game_manager = self
