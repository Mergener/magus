from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum
from re import T
from typing import Self, cast

import pygame as pg

from common.assets import Serializable, load_object_asset
from common.behaviour import get_behaviour_type_by_name, get_behaviour_type_name
from common.behaviours.network_behaviour import NetworkBehaviour
from common.network import DeliveryMode


class TargetMode(Enum):
    POINT = 0


@dataclass(eq=False)
class SpellInfo(Serializable):
    name: str
    tooltip: str
    cooldown: float
    target_mode: TargetMode
    state_behaviour: type[SpellState]
    data: dict
    _file_name: str

    @property
    def file_name(self):
        return self._file_name

    def serialize(self, out_dict: dict | None = None) -> dict:
        if out_dict is None:
            out_dict = {}

        out_dict["name"] = self.name
        out_dict["tooltip"] = self.tooltip
        out_dict["cooldown"] = self.cooldown
        out_dict["template_asset"] = self.template_asset
        out_dict["target_mode"] = self.target_mode.value
        out_dict["state_behaviour"] = get_behaviour_type_name(self.state_behaviour)
        out_dict["data"] = self.data

        return out_dict

    def deserialize(self, in_dict: dict) -> Self:
        self.name = in_dict.get("name", str())
        self.tooltip = in_dict.get("tooltip", str())
        self.cooldown = in_dict.get("cooldown", float())
        self.template_asset = in_dict.get("template_asset", str())
        self.target_mode = TargetMode(in_dict.get("target_mode", 0))
        self.data = in_dict.get("data", {})

        behaviour = get_behaviour_type_by_name(in_dict.get("state_behaviour"))
        if not isinstance(behaviour, SpellState):
            raise ValueError("Expected a spell state behaviour.")
        self.state_behaviour = cast(type[SpellState], behaviour)

        return self


class SpellState(NetworkBehaviour):
    _spell: SpellInfo

    def on_init(self):
        self.cooldown_timer = self.use_sync_var(
            float, delivery_mode=DeliveryMode.UNRELIABLE
        )

    def on_server_tick(self, tick_id: int):
        assert self.game
        tick_dt = self.game.simulation.tick_interval
        self.cooldown_timer.value = max(0, self.cooldown_timer.value - tick_dt)

    def on_client_update(self, dt: float):
        # Update cooldown in client for smooth updates.
        self.cooldown_timer.value = max(0, self.cooldown_timer.value - dt)

    @property
    def spell(self):
        return self._spell

    def can_cast_now(self):
        return self.cooldown_timer.value <= 0

    def can_cast_on_point_now(self, point: pg.Vector2):
        return self.can_cast_now()

    def on_point_cast(self, target: pg.Vector2):
        pass


def get_spell(file_name: str):
    spell_info = load_object_asset(f"spells/{file_name}.json", SpellInfo)
    spell_info._file_name = file_name
    return spell_info
