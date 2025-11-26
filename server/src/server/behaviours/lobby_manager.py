from __future__ import annotations

import asyncio

from common.assets import load_node_asset
from common.behaviour import Behaviour
from common.behaviours.network_entity_manager import NetworkEntityManager
from common.network import NetPeer
from game.entities import Entities
from game.lobby import (
    GameSceneLoaded,
    GameStarting,
    JoinGameRequest,
    JoinGameResponse,
    LobbyInfo,
    PlayerJoined,
    PlayerLeft,
    QuitLobby,
    StartGameRequest,
    UpdateLobbyInfo,
)
from game.player import Player


class LobbyManager(Behaviour):
    _entity_mgr: NetworkEntityManager | None

    @property
    def net_entity_manager(self):
        if self.game is None:
            return None

        if not hasattr("self", "_entity_mgr") or self._entity_mgr is None:
            self._entity_mgr = self.game.global_object.find_behaviour_in_children(
                NetworkEntityManager, recursive=True
            )
            if not self._entity_mgr:
                self._entity_mgr = self.game.scene.find_behaviour_in_children(
                    NetworkEntityManager, recursive=True
                )

        return self._entity_mgr

    def _handle_join_request(self, packet: JoinGameRequest, peer: NetPeer):
        assert self.game

        entity_manager = self.net_entity_manager
        if not entity_manager:
            return

        if len(self._players) >= self.lobby_info.capacity:
            peer.send(JoinGameResponse(False))
            return

        player_entity = entity_manager.spawn_entity("player")

        peer.send(JoinGameResponse(True))
        peer.send(PlayerJoined(player_entity.id, len(self._players), True))
        for i, p in enumerate(self._players):
            # Notify the player about every other present player.
            peer.send(PlayerJoined(p.net_entity.id, i, False))

        player_joined = PlayerJoined(player_entity.id, len(self._players), False)
        self.game.network.publish(player_joined, exclude_peers=[peer])

        player = player_entity.node.get_behaviour(Player)
        assert player
        player._handle_player_joined(player_joined)
        player._net_peer = peer

        self._players.append(player)

    async def _handle_start_game(self, packet: StartGameRequest, peer: NetPeer):
        assert self.game
        assert self.net_entity_manager

        self.game.network.publish(GameStarting())

        response_promise = self.game.network.expect_all(
            GameSceneLoaded, timeout_ms=20000
        )

        game_scene = load_node_asset("scenes/server/game.json")
        load_promise = self.game.load_scene_async(
            game_scene, [self.net_entity_manager.node] + [p.node for p in self._players]
        )

        responses = await asyncio.gather(response_promise, load_promise)
        # TODO: Handle player failing to load scene.
        self.net_entity_manager.spawn_entity(Entities.GAME_MANAGER.value)

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

    def _handle_update_lobby_info(self, packet: UpdateLobbyInfo, peer: NetPeer):
        self.lobby_info.update_from_packet(packet)

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
        self._update_lobby_info_handler = self.game.network.listen(
            UpdateLobbyInfo, lambda m, p: self._handle_update_lobby_info(m, p)
        )
        self._quit_lobby_handler = self.game.network.listen(
            QuitLobby, lambda _, p: self._handle_disconnection(p)
        )
        self._disconnection_handler = self.game.network.listen_disconnected(
            lambda p: self._handle_disconnection(p)
        )

    def on_destroy(self):
        assert self.game
        self.game.network.unlisten(JoinGameRequest, self._join_request_handler)
        self.game.network.unlisten(StartGameRequest, self._start_game_handler)
        self.game.network.unlisten(QuitLobby, self._quit_lobby_handler)
        self.game.network.unlisten_disconnected(self._disconnection_handler)
