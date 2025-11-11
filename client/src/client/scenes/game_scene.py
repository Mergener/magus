from client.behaviours.network_manager import NetworkManager
from client.behaviours.player import Player
from common.engine.behaviour import Behaviour
from common.engine.node import Node
from common.magus.packets import (
    JoinGameRequest,
    JoinGameResponse,
    NewGame,
    PlayerJoined,
)


class GameScene(Behaviour):
    _network_manager: NetworkManager

    def on_validate(self):
        return

    def on_start(self):
        if not self.game:
            return

        self._network_manager = self.node.add_behaviour(NetworkManager)
        self.game.network.publish(JoinGameRequest())
        self._join_game_listener = self.game.network.listen(
            JoinGameResponse, lambda resp, peer: self.on_game_joined()
        )

    def on_destroy(self):
        if not self.game:
            return

        if self._join_game_listener:
            self.game.network.unlisten(JoinGameResponse, self._join_game_listener)

    def on_game_joined(self):
        print("Game was succesfully joined!")

    def on_player_joined(self, msg: PlayerJoined):
        self.node.add_child().add_behaviour(Player)

    @property
    def network_manager(self):
        return self._network_manager


def make_game_scene() -> Node:
    return Node().add_behaviour(GameScene).node
