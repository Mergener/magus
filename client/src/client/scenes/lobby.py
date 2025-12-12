import json
from typing import cast

from common.assets import load_node_asset
from common.behaviour import Behaviour
from common.behaviours.network_entity_manager import NetworkEntityManager
from common.behaviours.ui.ui_button import UIButton
from common.behaviours.ui.ui_label import UILabel
from common.game import Game
from common.network import NetPeer
from common.utils import notnull
from game import player
from game.game_manager import GameManager
from game.lobby_base import (
    DoneLoadingGameScene,
    GameStarting,
    LobbyInfo,
    LobbyInfoPacket,
    PlayerJoined,
    QuitLobby,
    RequestLobbyInfo,
    StartGameRequest,
)
from game.player import Player


class Lobby(Behaviour):
    _local_player_index: int

    def on_pre_start(self):
        assert self.game

        self.play_button = self.node.get_child(1).get_or_add_behaviour(UIButton)
        self.back_button = self.node.get_child(2).get_or_add_behaviour(UIButton)

        self._lobby_info_label = self.node.get_child(3).get_or_add_behaviour(UILabel)

        self.back_button.on_click = lambda: self._on_back_button_pressed()
        self.play_button.on_click = lambda: cast(Game, self.game).network.publish(
            StartGameRequest()
        )

        self._player_joined_handler = self.game.network.listen(
            PlayerJoined, lambda p, _: self._on_player_joined(p)
        )
        self._game_starting_handler = self.game.network.listen(
            GameStarting, lambda p, _: self._on_game_starting(p)
        )
        self._lobby_info_handler = self.game.network.listen(
            LobbyInfoPacket, self._handle_lobby_info_packet
        )

        self._lobby_info: LobbyInfo = LobbyInfo()

    def on_start(self):
        assert self.game
        self.game.network.publish(RequestLobbyInfo())

    def on_destroy(self):
        assert self.game
        self.game.network.unlisten(PlayerJoined, self._player_joined_handler)
        self.game.network.unlisten(GameStarting, self._game_starting_handler)
        self.game.network.unlisten(LobbyInfoPacket, self._lobby_info_handler)

    def _on_player_joined(self, packet: PlayerJoined):
        for p in self._get_players():
            if (
                p.net_entity.id == packet.entity_id
                and packet.index == self._local_player_index
            ):
                p._local_player = True

        if self.game:
            self.game.network.publish(RequestLobbyInfo())

    async def _on_game_starting(self, packet: GameStarting):
        assert self.game
        game = self.game

        players = self._get_players()

        for p in players:
            if p.index == self._local_player_index:
                p._local_player = True

        player_nodes = [p.node for p in players]

        entity_mgr = notnull(self.game.container.get(NetworkEntityManager))

        await self.game.load_scene_async(
            load_node_asset("scenes/client/game.json"), player_nodes + [entity_mgr.node]
        )

        game.network.publish(DoneLoadingGameScene())

    def _on_back_button_pressed(self):
        assert self.game
        self.game.network.publish(QuitLobby())
        self.game.load_scene(load_node_asset("scenes/client/main_menu.json"))

    def _get_players(self):
        assert self.game
        players = self.game.scene.find_behaviours_in_children(Player, recursive=True)
        print(json.dumps(self.game.scene.serialize()))
        return players

    def _handle_lobby_info_packet(self, packet: LobbyInfoPacket, peer: NetPeer):
        assert self.game

        players = self._get_players()
        player_names = [p[0] for p in packet.players]
        for i, p in enumerate(players):
            if p.is_local_player():
                player_names[i] += " (you)"
                break

        self._lobby_info.from_packet(packet)
        self._lobby_info_label.text = (
            f"Players:\n       - {"\n       - ".join(player_names)}"
        )
        print("Got lobby info: ", self._lobby_info)
