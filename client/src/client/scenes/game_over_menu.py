from common.assets import load_node_asset
from common.behaviour import Behaviour
from common.behaviours.network_entity_manager import NetworkEntityManager
from common.behaviours.ui.ui_button import UIButton
from common.behaviours.ui.ui_label import UILabel
from common.utils import notnull
from game.game_manager import GameFinished


class GameOverMenu(Behaviour):
    _game_finished: GameFinished | None

    def on_init(self):
        self._game_finished = None

        self.winner_label = self.node.get_child(1).get_or_add_behaviour(UILabel)
        self.back_button = self.node.get_child(2).get_or_add_behaviour(UIButton)

        self.back_button.on_click = self._on_back_button

    def on_pre_start(self):
        assert self.game

    @property
    def game_finished(self):
        return self._game_finished

    @game_finished.setter
    def game_finished(self, value: GameFinished):
        self._game_finished = value
        self.winner_label.text = f"Team {value.winner_team + 1} victory!"

    async def _on_back_button(self):
        assert self.game
        game = self.game

        game.network.disconnect()

        await game.load_scene_async(load_node_asset("scenes/client/main_menu.json"))
