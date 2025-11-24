from typing import cast

from common.behaviour import Behaviour
from common.behaviours.ui.ui_button import UIButton
from common.game import Game


class Lobby(Behaviour):
    def on_start(self):
        self.play_button = self.node.get_child(1).get_or_add_behaviour(UIButton)
        self.exit_button = self.node.get_child(2).get_or_add_behaviour(UIButton)

        self.exit_button.on_click = lambda: cast(Game, self.game).quit()
        self.play_button.on_click = lambda: print("Play!")
