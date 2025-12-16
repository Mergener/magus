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

    def on_pre_start(self):
        assert self.game

        self.winner_label = self.node.get_child(1).get_or_add_behaviour(UILabel)
        self.back_button = self.node.get_child(2).get_or_add_behaviour(UIButton)

    @property
    def game_finished(self):
        return self._game_finished

    @game_finished.setter
    def game_finished(self, value: GameFinished):
        self._game_finished = value
        self.winner_label.text = f"Team {value.winner_team + 1} victory!"

    async def _on_back_button(self):
        assert self.game
        entity_mgr = self.game.container.get(NetworkEntityManager)
        game = self.game
        entity_mgr = notnull(self.game.container.get(NetworkEntityManager))
        await self.game.load_scene_async(
            load_node_asset("scenes/client/main_menu.json"), [entity_mgr.node]
        )

        if entity_mgr:
            entity_mgr.reset()
        game.network.purge()
        game.simulation.purge_futures()
