from sys import stderr
from typing import cast

from client.scenes.lobby import Lobby
from common.assets import load_node_asset
from common.behaviour import Behaviour
from common.behaviours.network_entity_manager import NetworkEntityManager
from common.behaviours.ui.ui_button import UIButton
from common.game import Game
from game.lobby_base import (
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
        self.play_button.on_click = lambda: self._join_game()

    async def _join_game(self):
        assert self.game

        self.game.network.publish(JoinGameRequest())
        response = await self.game.network.expect(JoinGameResponse)

        if response is None:
            print(
                "Failed to get response from server when trying to join game.",
                file=stderr,
            )
            return

        if not response.accepted:
            print("Join lobby request refused.")
            return

        lobby_node = load_node_asset("scenes/client/lobby.json")

        await self.game.load_scene_async(
            lobby_node,
            [p.node for p in self.game.scene.find_behaviours_in_children(Player, True)],
        )

        lobby = lobby_node.get_or_add_behaviour(Lobby)
        lobby._local_player_index = response.index

    def _on_join_game(self, msg: JoinGameResponse):
        assert self.game
