from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Self

from common.assets import Serializable
from common.behaviours.network_behaviour import NetworkBehaviour
from common.network import DeliveryMode


class TargetMode(Enum):
    POINT = 0


@dataclass(eq=False)
class SpellInfo(Serializable):
    name: str
    tooltip: str
    cooldown: float
    template_asset: str
    target_mode: TargetMode

    def serialize(self, out_dict: dict | None = None) -> dict:
        if out_dict is None:
            out_dict = {}

        out_dict["name"] = self.name
        out_dict["tooltip"] = self.tooltip
        out_dict["cooldown"] = self.cooldown
        out_dict["template_asset"] = self.template_asset
        out_dict["target_mode"] = self.target_mode.value

        return out_dict

    def deserialize(self, in_dict: dict) -> Self:
        self.name = in_dict.get("name", str())
        self.tooltip = in_dict.get("tooltip", str())
        self.cooldown = in_dict.get("cooldown", float())
        self.template_asset = in_dict.get("template_asset", str())
        self.target_mode = TargetMode(in_dict.get("target_mode", 0))

        return self


class SpellState(NetworkBehaviour):
    def on_init(self):
        self.cooldown_timer = self.use_sync_var(
            float, delivery_mode=DeliveryMode.UNRELIABLE
        )

    def on_server_tick(self, tick_id: int):
        assert self.game
        tick_dt = self.game.simulation.tick_interval
        self.cooldown_timer.value -= tick_dt

    def on_client_update(self, dt: float):
        # Update cooldown in client for smooth updates.
        self.cooldown_timer.value -= dt
