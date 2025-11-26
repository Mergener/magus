from typing import cast

from common.assets import load_node_asset
from common.behaviour import Behaviour
from common.behaviours.network_entity_manager import NetworkEntityManager
from common.behaviours.ui.ui_button import UIButton
from common.game import Game
from game.lobby import GameStarting, PlayerJoined, QuitLobby, StartGameRequest
from game.player import Player


class Lobby(Behaviour):
    def on_pre_start(self):
        assert self.game

        self.play_button = self.node.get_child(1).get_or_add_behaviour(UIButton)
        self.back_button = self.node.get_child(2).get_or_add_behaviour(UIButton)

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

        entity_mgr = self.game.scene.find_behaviour_in_children(NetworkEntityManager)
        if entity_mgr is None:
            self.game.scene.add_child().add_behaviour(NetworkEntityManager)

    def on_destroy(self):
        assert self.game
        self.game.network.unlisten(PlayerJoined, self._player_joined_handler)
        self.game.network.unlisten(GameStarting, self._game_starting_handler)

    def _on_player_joined(self, packet: PlayerJoined):
        print("A new player joined!")

    def _on_game_starting(self, packet: GameStarting):
        assert self.game

        players = [
            p.node
            for p in self.game.scene.find_behaviours_in_children(Player, recursive=True)
        ]
        entity_mgr = self.game.scene.find_behaviour_in_children(NetworkEntityManager)
        assert entity_mgr

        self.game.load_scene(
            load_node_asset("scenes/client/game.json"), players + [entity_mgr.node]
        )

    def _on_back_button_pressed(self):
        assert self.game
        self.game.network.publish(QuitLobby())
        self.game.load_scene(load_node_asset("scenes/client/main_menu.json"))
