from typing import cast

from common.assets import load_node_asset
from common.behaviour import Behaviour
from common.behaviours.network_entity_manager import NetworkEntityManager
from common.behaviours.ui.ui_button import UIButton
from common.game import Game
from game.lobby import (
    GameStarting,
    JoinGameRequest,
    JoinGameResponse,
    PlayerJoined,
    StartGameRequest,
)
from game.player import Player


class MainMenu(Behaviour):
    def on_pre_start(self):
        assert self.game

        self.play_button = self.node.get_child(1).get_or_add_behaviour(UIButton)
        self.exit_button = self.node.get_child(2).get_or_add_behaviour(UIButton)

        self.exit_button.on_click = lambda: cast(Game, self.game).quit()
        self.play_button.on_click = lambda: cast(Game, self.game).network.publish(
            JoinGameRequest()
        )
        self._join_game_handler = self.game.network.listen(
            JoinGameResponse, lambda msg, _: self._on_join_game(msg)
        )

    def _on_join_game(self, msg: JoinGameResponse):
        assert self.game
        if not msg.accepted:
            print("Join lobby request refused.")
            return
        self.game.load_scene(load_node_asset("scenes/client/lobby.json"))

    def on_destroy(self):
        assert self.game
        self.game.network.unlisten(JoinGameResponse, self._join_game_handler)
