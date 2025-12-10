from __future__ import annotations

import random
from collections import defaultdict
from typing import TYPE_CHECKING, Any

import pygame as pg

from common.behaviour import Behaviour
from common.behaviours.network_behaviour import (
    NetworkBehaviour,
    client_method,
    entity_packet_handler,
    server_method,
)
from common.behaviours.singleton_behaviour import SingletonBehaviour
from common.binary import ByteReader, ByteWriter
from common.network import DeliveryMode, NetPeer, Packet
from common.primitives import Vector2
from common.utils import notnull
from game.lobby_base import LobbyInfo

if TYPE_CHECKING:
    from game.player import Player


SUPER_KEYS = [
    pg.K_LSUPER,
    pg.K_RSUPER,
    pg.K_LMETA,
    pg.K_RMETA,
]


class RoundFinished(Packet):
    def __init__(self, winner_team: int):
        self.winner_team = winner_team

    def on_write(self, writer: ByteWriter):
        writer.write_uint16(self.winner_team)

    def on_read(self, reader: ByteReader):
        self.winner_team = reader.read_uint16()

    @property
    def delivery_mode(self):
        return DeliveryMode.RELIABLE_ORDERED


class GameFinished(Packet):
    def __init__(self, winner_team: int):
        self.winner_team = winner_team

    def on_write(self, writer: ByteWriter):
        writer.write_uint16(self.winner_team)

    def on_read(self, reader: ByteReader):
        self.winner_team = reader.read_uint16()

    @property
    def delivery_mode(self):
        return DeliveryMode.RELIABLE_ORDERED


class RoundStarting(Packet):
    def on_write(self, writer: ByteWriter):
        pass

    def on_read(self, reader: ByteReader):
        pass

    @property
    def delivery_mode(self):
        return DeliveryMode.RELIABLE_ORDERED


class GameManager(NetworkBehaviour):
    def on_init(self) -> Any:
        self._players: list[Player] = []
        self._players_by_peer: dict[NetPeer, Player] = {}
        self._round = self.use_sync_var(int, 1)
        self._team_wins: defaultdict[int, int] = defaultdict(int)

    @property
    def round(self):
        return self._round

    @property
    def players(self):
        return self._players

    def get_player_by_index(self, player_idx: int):
        if player_idx not in range(len(self._players)):
            return None
        return self._players[player_idx]

    def get_player_by_peer(self, peer: NetPeer):
        return self._players_by_peer[peer]

    @client_method
    def get_local_player(self):
        for p in self.players:
            if p.local_player():
                return p
        raise Exception("Expected a local player")

    @server_method
    def on_player_death(self, player: Player, killer_player: Player | None):
        player.deaths.value += 1
        if killer_player:
            killer_player.kills.value += 1

    #
    # Private
    #

    @client_method
    def _on_round_finished(self, packet: RoundFinished, peer: NetPeer):
        pass

    #
    # Lifecycle
    #

    def on_common_pre_start(self):
        assert self.game
        self.game.container.register_singleton(type(self), self)
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

    def on_client_pre_start(self) -> Any:
        assert self.game
        self._round_finished_listener = self.game.network.listen(
            RoundFinished, self._on_round_finished
        )

    def on_client_start(self):
        pg.event.set_grab(True)

    def on_client_update(self, dt: float):
        assert self.game

        for k in SUPER_KEYS:
            if self.game.input.is_key_just_pressed(k):
                pg.event.set_grab(False)

    def on_destroy(self):
        assert self.game
        self.game.container.unregister(type(self))
        if hasattr(self, "_round_finished_listener"):
            self.game.network.unlisten(RoundFinished, self._round_finished_listener)
