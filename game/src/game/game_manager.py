from __future__ import annotations

import json
import random
from collections import defaultdict
from typing import TYPE_CHECKING, Any

import pygame as pg

import server
from common.assets import load_node_asset
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
        self._local_player: Player | None = None
        self._players: list[Player] | None = None
        self._players_by_peer: dict[NetPeer, Player] | None = None
        self._round = self.use_sync_var(int, 1)
        self._team_wins: defaultdict[int, int] = defaultdict(int)

    def get_team_wins(self, team: int):
        return self._team_wins.get(team, 0)

    @property
    def round(self):
        return self._round

    @property
    def players(self):
        self._refresh_players_registry()
        return notnull(self._players)

    def _refresh_players_registry(self):
        from game.player import Player

        assert self.game

        if self._players is None:
            self._players = self.game.scene.get_behaviours_in_children(
                Player, recursive=True
            )

        if self._players_by_peer is None and self.game.network.is_server():
            self._players_by_peer = {}
            for p in self._players:
                if p.net_peer is None:
                    continue
                self._players_by_peer[p.net_peer] = p

    def get_player_by_index(self, player_idx: int):
        self._refresh_players_registry()
        if player_idx not in range(len(self.players)):
            return None
        return self.players[player_idx]

    @server_method
    def get_player_by_peer(self, peer: NetPeer):
        self._refresh_players_registry()

        assert self._players_by_peer

        return self._players_by_peer[peer]

    @client_method
    def get_local_player(self):
        self._refresh_players_registry()

        if self._local_player is None:
            for p in self.players:
                if p.is_local_player():
                    self._local_player = p

        return self._local_player

    @server_method
    def on_player_death(self, player: Player, killer_player: Player | None):
        assert self.game
        player.deaths.value += 1
        if killer_player:
            killer_player.kills.value += 1

        alive_teams = set()
        for p in self.players:
            if not p.mage:
                continue

            if p.mage.alive:
                alive_teams.add(p.team.value)

        if len(alive_teams) == 1:
            self.game.simulation.run_task(self._finish_round(alive_teams.pop()))

    #
    # Private
    #

    @server_method
    async def _finish_round(self, winner_team: int):
        assert self.game
        self.game.network.publish(RoundFinished(winner_team))
        for p in self.players:
            mage = p.mage
            if not mage:
                continue

            if not mage.alive:
                mage.revive()

            mage.transform.position = Vector2(
                random.randint(-200, 200), random.randint(-200, 200)
            )

        await self.game.simulation.wait_seconds(30)
        self._start_round()

    @server_method
    def _start_round(self):
        assert self.game
        self.game.network.publish(RoundStarting())
        for p in self.players:
            mage = p.mage
            if not mage:
                continue

            mage.transform.position = Vector2(
                random.randint(-200, 200), random.randint(-200, 200)
            )

    @client_method
    def _on_round_finished(self, packet: RoundFinished, peer: NetPeer):
        pass

    #
    # Lifecycle
    #

    def on_common_pre_start(self):
        self._refresh_players_registry()

        assert self.game
        self.game.container.register_singleton(type(self), self)

    def on_server_start(self):
        from game.mage import Mage

        for p in self.players:
            mage = self.entity_manager.spawn_entity("mage").node.get_or_add_behaviour(
                Mage
            )
            mage.owner_index.value = p.index
            p.mage_entity_id.value = mage.net_entity.id
            p._mage = mage
            p._game_manager = self

        self._start_round()

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
