from common.behaviour import Behaviour
from common.behaviours.network_entity_manager import SpawnEntity
from common.behaviours.ui.ui_button import UIButton
from common.behaviours.ui.ui_image import UIImage
from common.primitives import Vector2
from game.game_manager import GameManager
from game.mage import AddSpell, Mage


class Hud(Behaviour):
    _mage: Mage | None

    def on_init(self):
        self._spell_buttons: list[UIButton] = []
        self._mage = None
        self._spell_icon_dimensions = Vector2(64, 64)
        self._spell_icon_padding = 10

    def on_pre_start(self):
        assert self.game
        self._add_spell_handler = self.game.network.listen(
            AddSpell, lambda _, __: self._refresh_buttons()
        )

    def on_tick(self, tick_id: int):
        if self.mage:
            return

        assert self.game

        game_mgr = self.game.container.get(GameManager)
        if not game_mgr:
            return

        player = game_mgr.get_local_player()
        if not player:
            return

        mage = player.mage
        if not mage:
            return

        self.mage = mage

    def on_destroy(self):
        assert self.game
        self.game.network.unlisten(AddSpell, self._add_spell_handler)

    @property
    def mage(self):
        return self._mage

    @mage.setter
    def mage(self, value: Mage | None):
        self._mage = value
        self._refresh_buttons()

    def _refresh_buttons(self):
        for b in self._spell_buttons:
            b.node.destroy()

        self._spell_buttons.clear()

        if self.mage is None:
            return

        start_x = (
            -len(self.mage.spells)
            / 2
            * (self._spell_icon_dimensions.x + self._spell_icon_padding)
        )
        y = self.transform.local_position.y

        for i, spell_state in enumerate(self.mage.spells):
            print(spell_state.spell.base_icon.path)
            node = self.node.add_child()
            node.skip_serialization = True
            icon = node.add_behaviour(UIImage)
            icon.image_asset = spell_state.spell.base_icon
            icon.anchor = Vector2(0.5, 0.05)
            icon.transform.local_position = Vector2(
                start_x
                + i * (self._spell_icon_dimensions.x + self._spell_icon_padding),
                y,
            )
            icon.dimensions = self._spell_icon_dimensions

    def on_serialize(self, out_dict: dict):
        out_dict["spell_icon_dimensions"] = self._spell_icon_dimensions.serialize()
        out_dict["spell_icon_padding"] = self._spell_icon_padding

    def on_deserialize(self, in_dict: dict):
        self._spell_icon_dimensions.deserialize(
            in_dict.get("spell_icon_dimensions"), Vector2(64, 64)
        )
        self._spell_icon_padding = in_dict.get("spell_icon_padding", 10)
