import pygame as pg

from client.cooldown_mask import CooldownMask
from common.node import Node
from pygame.draw import line

from common.behaviour import Behaviour
from common.behaviours.network_entity_manager import SpawnEntity
from common.behaviours.ui.ui_button import UIButton
from common.behaviours.ui.ui_image import UIImage
from common.behaviours.ui.ui_label import UILabel, HorizontalAlign
from common.primitives import Color, Vector2
from game.game_manager import GameManager, RoundFinished
from game.mage import AddSpell, Mage


class Hud(Behaviour):
    _mage: Mage | None

    def on_init(self):
        self._mage = None
        self._spell_buttons: list[Node] = []
        self._spell_icon_dimensions = Vector2(64, 64)
        self._spell_icon_padding = 10

    def on_pre_start(self):
        assert self.game
        self._add_spell_handler = self.game.network.listen(
            AddSpell, lambda _, __: self._refresh_buttons()
        )
        self._scoreboard_label = self.node.get_child(0).get_or_add_behaviour(UILabel)

    def on_start(self):
        self._refresh_scoreboard()

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

        for p in game_mgr.players:
            p.kills.add_hook(lambda _, __: self._refresh_scoreboard())
            p.deaths.add_hook(lambda _, __: self._refresh_scoreboard())
            p.team.add_hook(lambda _, __: self._refresh_scoreboard())

        self._refresh_scoreboard()

        self.mage = mage
        
        self._round_finished_handler = self.game.network.listen(
            RoundFinished, lambda _, __: self._refresh_scoreboard()
        )

    def on_destroy(self):
        assert self.game
        self.game.network.unlisten(AddSpell, self._add_spell_handler)
        
        if hasattr(self, "_round_finished_handler"):
            self.game.network.unlisten(RoundFinished, self._round_finished_handler)

    @property
    def mage(self):
        return self._mage

    @mage.setter
    def mage(self, value: Mage | None):
        self._mage = value
        self._refresh_buttons()

    def _refresh_buttons(self):
        if self.mage is None:
            return
        
        for sb in self._spell_buttons:
            sb.destroy()
            
        self._spell_buttons.clear()

        start_x = (
            -len(self.mage.spells)
            / 2
            * (self._spell_icon_dimensions.x + self._spell_icon_padding)
        )
        y = self.transform.local_position.y

        for i, spell_state in enumerate(self.mage.spells):
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
            self._spell_buttons.append(node)
            
            cd_mask = node.add_child().add_behaviour(CooldownMask)
            cd_mask.spell_state = spell_state
            cd_mask.surface.render_layer = icon.render_layer + 1
            cd_mask.surface.anchor = icon.anchor
            
            surf = pg.Surface(self._spell_icon_dimensions, pg.SRCALPHA).convert_alpha()
            surf.fill(Color(0, 0, 0, 160))
            cd_mask.surface.set_surface(surf)
            
            cd_mask.label.horizontal_align = HorizontalAlign.LEFT
            cd_mask.label.anchor = icon.anchor
            cd_mask.label.render_layer = icon.render_layer + 2

    def _refresh_scoreboard(self):
        assert self.game
        game_mgr = self.game.container.get(GameManager)
        if not game_mgr:
            return

        lines = ["Scoreboard"]
        teams = sorted(list(set(p.team.value for p in game_mgr.players)))
        for t in teams:
            lines.append(f"Team {t + 1} ({game_mgr.get_team_wins(t)} of {game_mgr.max_rounds} round wins)")
            for p in game_mgr.players:
                if p.team.value != t:
                    continue
                lines.append(
                    f"\t{p.player_name.value} {"(you) " if p.is_local_player() else ""}[{p.kills.value}/{p.deaths.value}]"
                )
            lines.append("")

        self._scoreboard_label.text = "\n".join(lines)

    def on_serialize(self, out_dict: dict):
        out_dict["spell_icon_dimensions"] = self._spell_icon_dimensions.serialize()
        out_dict["spell_icon_padding"] = self._spell_icon_padding

    def on_deserialize(self, in_dict: dict):
        self._spell_icon_dimensions.deserialize(
            in_dict.get("spell_icon_dimensions"), Vector2(64, 64)
        )
        self._spell_icon_padding = in_dict.get("spell_icon_padding", 10)
