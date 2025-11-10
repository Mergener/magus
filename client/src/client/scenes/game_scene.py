from common.behaviour import Behaviour
from common.network import NetPeer
from common.node import Node
from common.packets import JoinGameRequest, JoinGameResponse, NewGame


class GameScene(Behaviour):
    def on_init(self):
        return

    def on_start(self):
        if not self.game:
            return

        self.game.network.publish(JoinGameRequest())
        self._join_game_listener = self.game.network.listen(
            JoinGameResponse, lambda resp, peer: self.on_game_joined(resp, peer)
        )

    def on_destroy(self):
        if not self.game:
            return

        if self._join_game_listener:
            self.game.network.unlisten(JoinGameResponse, self._join_game_listener)

    def on_game_joined(self, msg: JoinGameResponse, server: NetPeer):
        print("Game was succesfully joined!")


def make_game_scene() -> Node:
    return Node().add_behaviour(GameScene).node
