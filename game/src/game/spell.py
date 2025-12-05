from __future__ import annotations

import re
from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from re import T
from typing import TYPE_CHECKING, Self, cast, final

import pygame as pg

from common.assets import Serializable, load_object_asset
from common.behaviour import get_behaviour_type_by_name, get_behaviour_type_name
from common.behaviours.network_behaviour import NetworkBehaviour
from common.network import DeliveryMode
from common.utils import get_object_attribute_from_dotted_path, notnull

if TYPE_CHECKING:
    from game.mage import Mage


class TargetMode(Enum):
    POINT = 0


_PLACEHOLDER_PATTERN = re.compile(r"%([a-zA-Z0-9_.]+)%")


@dataclass(eq=False)
@final
class SpellInfo(Serializable):
    name: str
    levels: int
    target_mode: TargetMode
    state_behaviour: type[SpellState]
    cooldown: list[float] = field(default_factory=lambda: [0])
    data: dict = field(default_factory=dict)
    _raw_tooltip: str = field(default_factory=str)
    _file_name: str = field(default_factory=str)
    _formatted_tooltip_cache: dict[int, str] = field(default_factory=dict)

    @property
    def file_name(self):
        return self._file_name

    def serialize(self, out_dict: dict | None = None) -> dict:
        if out_dict is None:
            out_dict = {}

        out_dict["name"] = self.name
        out_dict["tooltip"] = self._raw_tooltip
        out_dict["levels"] = self.levels
        out_dict["cooldown"] = self.cooldown
        out_dict["target_mode"] = self.target_mode.value
        out_dict["state_behaviour"] = get_behaviour_type_name(self.state_behaviour)
        out_dict["data"] = self.data

        return out_dict

    def deserialize(self, in_dict: dict) -> Self:
        print("Calling deserialize for spell info")
        self.name = in_dict.get("name", str())
        self._raw_tooltip = in_dict.get("tooltip", str())
        self.levels = in_dict.get("levels", 1)

        dict_cooldown = in_dict.get("cooldown", [0])
        assert isinstance(dict_cooldown, list | int | float)
        if isinstance(dict_cooldown, int | float):
            dict_cooldown = [float(dict_cooldown)]
        self.cooldown = dict_cooldown

        self.target_mode = TargetMode(in_dict.get("target_mode", 0))
        self.data = in_dict.get("data", {})

        behaviour = get_behaviour_type_by_name(in_dict.get("state_behaviour"))
        print("Got behaviour", behaviour)
        if behaviour is None or not issubclass(behaviour, SpellState):
            raise ValueError("Expected a spell state behaviour.")
        self.state_behaviour = cast(type[SpellState], behaviour)

        # Ensure all fields are set
        self._file_name = ""
        self._formatted_tooltip_cache = {}

        return self

    def _generate_formatted_tooltip(self, level: int):
        tooltip = self._raw_tooltip

        def replacer(match):
            path = match.group(1)
            return get_object_attribute_from_dotted_path(self, path, level)

        return _PLACEHOLDER_PATTERN.sub(replacer, tooltip)

    def get_formatted_tooltip(self, level: int):
        cached = self._formatted_tooltip_cache.get(level)
        if cached:
            return

        tooltip = self._generate_formatted_tooltip(level)
        self._formatted_tooltip_cache[level] = tooltip
        return tooltip


class SpellState(NetworkBehaviour):
    _mage: Mage
    _spell: SpellInfo

    def on_init(self):
        self.cooldown_timer = self.use_sync_var(
            float, delivery_mode=DeliveryMode.UNRELIABLE
        )
        self.level = self.use_sync_var(int, 1)

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
        if self.spell.target_mode != TargetMode.POINT:
            return False

        return self.can_cast_now()

    def on_point_cast(self, target: pg.Vector2):
        pass


def get_spell(file_name: str):
    spell_info = load_object_asset(f"spells/{file_name}.json", SpellInfo)
    print("Loaded spell info here!", spell_info.__dict__)
    spell_info._file_name = file_name
    return spell_info
