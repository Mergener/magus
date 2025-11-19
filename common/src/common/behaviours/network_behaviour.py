from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, cast

from common.behaviour import Behaviour
from common.network import CombinedPacket, DeliveryMode
from common.packets import SyncVarPacket

if TYPE_CHECKING:
    from common.behaviours.network_entity import NetworkEntity


class NetworkBehaviour(Behaviour, ABC):
    _sync_vars: list[SyncVarState]

    @property
    def net_entity(self):
        from common.behaviours.network_entity import NetworkEntity

        if self._net_entity is None:  # type: ignore
            self._net_entity = self.node.get_or_add_behaviour(NetworkEntity)
        return self._net_entity

    def use_sync_var[
        T
    ](self, var_type: SyncVarType, initial_value: T) -> SyncVarState[T]:
        if not hasattr(self, "_sync_vars"):
            self._sync_vars = []

        sync_var = SyncVarState[T](var_type, initial_value)
        self._sync_vars.append(sync_var)
        return sync_var

    def on_tick(self, tick_id: int):
        if not hasattr(self, "_sync_vars"):
            self._sync_vars = []

        self._server_tick(tick_id)
        self._client_tick(tick_id)

    def _client_tick(self, tick_id: int):
        assert self.game
        if not self.game.network.is_client():
            return

    def _server_tick(self, tick_id: int):
        assert self.game
        if not self.game.network.is_server():
            return

        packet_to_send: CombinedPacket | None = None
        for v in self._sync_vars:
            if v.value != v._last_updated_value:
                if packet_to_send is None:
                    packet_to_send = CombinedPacket([])
                packet_to_send.packets.append(
                    SyncVarPacket(
                        self.net_entity.id, v._var_type, v.value, tick_id, v.reliability
                    )
                )


class SyncVarType(Enum):
    INT8 = (0,)
    INT16 = (1,)
    INT32 = (2,)
    INT64 = (3,)
    UINT8 = (4,)
    UINT16 = (5,)
    UINT32 = (6,)
    UINT64 = (7,)
    FLOAT32 = (8,)
    FLOAT64 = (9,)
    STR = 10


class SyncVarState[T]:
    def __init__(
        self,
        var_type: SyncVarType,
        value: T,
        reliability: DeliveryMode = DeliveryMode.RELIABLE,
    ):
        self.value = value
        self.reliability = reliability
        self._var_type = var_type
        self._last_updated_tick = -1
        self._last_updated_value = value
