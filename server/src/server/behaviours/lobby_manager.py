from __future__ import annotations

from typing import cast

from common.assets import load_node_asset
from common.behaviour import Behaviour
from common.behaviours.network_entity_manager import NetworkEntityManager
from common.binary import ByteReader, ByteWriter
from common.network import DeliveryMode, NetPeer, Packet
from game.lobby import (
    JoinGameRequest,
    JoinGameResponse,
    LobbyInfo,
    PlayerJoined,
    StartGameRequest,
    UpdateLobbyInfo,
)
from game.player import Player


class LobbyManager(Behaviour):
    _entity_mgr: NetworkEntityManager | None

    def on_init(self):
        self._players: list[Player] = []

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

    def on_start(self):
        assert self.game

        print("Started!")

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

        player_joined = PlayerJoined(player_entity.id, len(self._players), False)
        self.game.network.publish(player_joined, exclude_peers=[peer])
        player = player_entity.node.get_behaviour(Player)
        assert player
        player._handle_player_joined(player_joined)

        self._players.append(player)

    def _handle_start_game(self, packet: StartGameRequest, peer: NetPeer):
        assert self.game
        assert self.net_entity_manager
        game_scene = load_node_asset("scenes/server/game.json")
        self.game.load_scene(
            game_scene, [self.net_entity_manager.node] + [p.node for p in self._players]
        )

    def _handle_update_lobby_info(self, packet: UpdateLobbyInfo, peer: NetPeer):
        self.lobby_info.update_from_packet(packet)

    def on_destroy(self):
        assert self.game
        self.game.network.unlisten(JoinGameRequest, self._handle_join_request)
        self.game.network.unlisten(StartGameRequest, self._handle_start_game)
