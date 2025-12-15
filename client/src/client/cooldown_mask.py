from typing import Any

from pygame import Color

from common.behaviour import Behaviour
from common.behaviours.ui.ui_label import HorizontalAlign, UILabel
from common.behaviours.ui.ui_surface import UISurface
from common.primitives import Vector2
from game.spell import SpellState


class CooldownMask(Behaviour):
    spell_state: SpellState | None

    def on_init(self) -> Any:
        self.surface = self.node.add_child().add_behaviour(UISurface)
        label_node = self.node.add_child()
        label_node.transform.local_position = Vector2(-100, 0)
        self.label = label_node.add_behaviour(UILabel)
        self.label.horizontal_align = HorizontalAlign.RIGHT
        self.label.color = Color(255, 255, 255, 255)
        self.surface.visible = False
        self.label.visible = False

        self.spell_state = None

    def on_tick(self, tick_id: int) -> Any:
        if self.spell_state is None:
            return

        cd = self.spell_state.cooldown_timer.value
        if cd <= 0:
            self.surface.visible = False
            self.label.text = ""
            return

        self.surface.visible = True
        self.label.text = str(int(cd))
