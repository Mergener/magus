from __future__ import annotations

import asyncio
import json

from common.assets import load_node_asset
from common.behaviour import Behaviour
from common.behaviours.network_entity_manager import NetworkEntityManager
from common.network import NetPeer
from game.game_manager import GameManager
from game.lobby_base import (
    DoneLoadingGameScene,
    GameStarting,
    JoinGameRequest,
    JoinGameResponse,
    LobbyInfo,
    LobbyInfoPacket,
    PlayerJoined,
    PlayerLeft,
    QuitLobby,
    RequestLobbyInfo,
    StartGameRequest,
)
from game.player import Player


class LobbyManager(Behaviour):
    @property
    def net_entity_manager(self):
        if self.game is None:
            return None

        return self.game.container.get(NetworkEntityManager)

    def _handle_join_request(self, packet: JoinGameRequest, peer: NetPeer):
        assert self.game

        entity_manager = self.net_entity_manager
        if not entity_manager:
            return

        if len(self._players) >= self.lobby_info.capacity:
            peer.send(JoinGameResponse(False, 0))
            return

        player_entity = entity_manager.spawn_entity("player")

        peer.send(JoinGameResponse(True, len(self._players)))
        peer.send(PlayerJoined(player_entity.id, len(self._players), True))
        for i, p in enumerate(self._players):
            # Notify the player about every other present player.
            peer.send(PlayerJoined(p.net_entity.id, i, False))

        player_joined = PlayerJoined(player_entity.id, len(self._players), False)
        self.game.network.publish(player_joined, exclude_peers=[peer])

        player = player_entity.node.get_behaviour(Player)
        assert player
        player._handle_player_joined(player_joined, peer)
        player._net_peer = peer
        player.index = len(self._players)
        player.team.value = player.index

        self._players.append(player)
        self._refresh_players()

    async def _handle_start_game(self, packet: StartGameRequest, peer: NetPeer):
        assert self.game
        assert self.net_entity_manager
        entity_mgr = self.net_entity_manager

        self.game.network.publish(GameStarting())

        response_promise = self.game.network.expect_all(
            DoneLoadingGameScene, timeout_ms=20000
        )

        game_scene = load_node_asset("scenes/server/game.json")
        load_promise = self.game.load_scene_async(
            game_scene, [entity_mgr.node] + [p.node for p in self._players]
        )

        await asyncio.gather(response_promise, load_promise)

        # TODO: Handle player failing to load scene.
        game_mgr_node = entity_mgr.spawn_entity("game_manager").node
        game_mgr = game_mgr_node.get_or_add_behaviour(GameManager)
        game_mgr._players = self._players

    def _handle_disconnection(self, peer):
        assert self.game

        player = None
        for i, p in enumerate(self._players):
            if p.net_peer == peer:
                player = p
                del self._players[i]
                break

        if player is None:
            return

        player_left = PlayerLeft(player.net_entity.id, player.index)
        self.game.network.publish(player_left)
        self._refresh_players()

    def _refresh_players(self):
        for i, p in enumerate(self._players):
            p.index = i
            p.team.value = i
            p.player_name.value = f"Player {p.index + 1}"

        self.lobby_info.players = [
            (p.player_name.value, p.index, p.team.value) for p in self._players
        ]

        if self.game:
            self.game.network.publish(self.lobby_info.to_packet())

    def _handle_update_lobby_info(self, packet: LobbyInfoPacket, peer: NetPeer):
        if not self.game or self.game.network.is_server():
            return

        self.lobby_info.from_packet(packet)

    def _handle_lobby_info_request(self, packet: RequestLobbyInfo, peer: NetPeer):
        peer.send(self.lobby_info.to_packet())

    def on_init(self):
        self._players: list[Player] = []

    def on_pre_start(self):
        assert self.game

        self.lobby_info = LobbyInfo()

        self._join_request_handler = self.game.network.listen(
            JoinGameRequest, lambda m, p: self._handle_join_request(m, p)
        )
        self._start_game_handler = self.game.network.listen(
            StartGameRequest, lambda m, p: self._handle_start_game(m, p)
        )
        self._lobby_info_packet_handler = self.game.network.listen(
            LobbyInfoPacket, lambda m, p: self._handle_update_lobby_info(m, p)
        )
        self._quit_lobby_handler = self.game.network.listen(
            QuitLobby, lambda _, p: self._handle_disconnection(p)
        )
        self._lobby_info_req_handler = self.game.network.listen(
            RequestLobbyInfo,
            lambda packet, peer: self._handle_lobby_info_request(packet, peer),
        )
        self._disconnection_handler = self.game.network.listen_disconnected(
            lambda p: self._handle_disconnection(p)
        )

    def on_destroy(self):
        assert self.game
        self.game.network.unlisten(JoinGameRequest, self._join_request_handler)
        self.game.network.unlisten(StartGameRequest, self._start_game_handler)
        self.game.network.unlisten(QuitLobby, self._quit_lobby_handler)
        self.game.network.unlisten(RequestLobbyInfo, self._lobby_info_req_handler)
        self.game.network.unlisten_disconnected(self._disconnection_handler)
