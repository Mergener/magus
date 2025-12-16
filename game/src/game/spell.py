from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Self, cast, final

from common.assets import ImageAsset, Serializable, load_image_asset, load_object_asset
from common.behaviour import get_behaviour_type_by_name, get_behaviour_type_name
from common.behaviours.camera import Camera
from common.behaviours.network_behaviour import NetworkBehaviour
from common.network import DeliveryMode
from common.primitives import Vector2
from common.utils import get_object_attribute_from_dotted_path
from game.orders import OrderTransition

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
    base_icon: ImageAsset = field(default=ImageAsset(None, "null"))
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

        if self.base_icon:
            out_dict["base_icon"] = self.base_icon.serialize()

        return out_dict

    def deserialize(self, in_dict: dict) -> Self:
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
        if behaviour is None or not issubclass(behaviour, SpellState):
            raise ValueError("Expected a spell state behaviour.")
        self.state_behaviour = cast(type[SpellState], behaviour)

        # Ensure all fields are set
        self._file_name = ""
        self._formatted_tooltip_cache = {}

        base_icon_data = in_dict.get("base_icon")
        if base_icon_data is not None:
            self.base_icon.deserialize(base_icon_data)

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

    def get_level_data[T](self, entry: str, level: int, fallback: T) -> T:
        self.data.get(entry)

        data = self.data.get(entry)

        if isinstance(data, list):
            data = data[min(len(data) - 1, level - 1)]

        if data is None:
            return fallback

        return data

    def get_level_cooldown(self, level: int):
        return self.cooldown[min(len(self.cooldown) - 1, level - 1)]

class SpellState(NetworkBehaviour):
    _mage: Mage
    _spell: SpellInfo
    _hotkey: int | None

    def on_init(self):
        self.cooldown_timer = self.use_sync_var(
            float, delivery_mode=DeliveryMode.UNRELIABLE
        )
        self.level = self.use_sync_var(int, 1)

    def get_point_cast_order(self, mage: Mage, where: Vector2):
        def point_cast_order():
            mage.face(where)
            if mage.animator:
                mage.animator.play("cast")
            self.cooldown_timer.value = self.get_current_level_cooldown()
            self.on_point_cast(where)
            yield OrderTransition.CONTINUE

        return point_cast_order()

    def get_formatted_tooltip(self):
        return self.spell.get_formatted_tooltip(self.level.value)

    @property
    def spell(self):
        return self._spell

    def can_cast_now(self):
        return self.cooldown_timer.value <= 0

    def can_cast_on_point_now(self, point: Vector2):
        if self.spell.target_mode != TargetMode.POINT:
            return False

        return self.can_cast_now()

    def on_point_cast(self, target: Vector2):
        pass

    def get_current_level_cooldown(self):
        return self.spell.get_level_cooldown(self.level.value)

    def get_current_level_data[T](self, entry: str, fallback: T) -> T:
        return self.spell.get_level_data(entry, self.level.value, fallback)

    def on_server_tick(self, tick_id: int):
        assert self.game
        tick_dt = self.game.simulation.tick_interval
        self.cooldown_timer.value = max(0, self.cooldown_timer.value - tick_dt)

    def on_client_update(self, dt: float):
        assert self.game

        # Update cooldown in client for smooth updates.
        self.cooldown_timer.value = max(0, self.cooldown_timer.value - dt)

        if self._hotkey and self.game.input.is_key_just_released(self._hotkey):
            from game.mage import CastPointTargetSpellOrder

            camera = self.game.container.get(Camera)
            if camera is None:
                return

            mouse_world_pos = camera.screen_to_world_space(self.game.input.mouse_pos)
            if self.spell.target_mode == TargetMode.POINT:
                self.game.network.publish(
                    CastPointTargetSpellOrder(
                        self._mage.net_entity.id, self.net_entity.id, mouse_world_pos
                    )
                )


def get_spell(file_name: str):
    spell_info = load_object_asset(f"spells/{file_name}.json", SpellInfo)
    spell_info._file_name = file_name
    return spell_info
