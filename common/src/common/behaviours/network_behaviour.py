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
    @property
    def net_entity(self):
        from common.behaviours.network_entity import NetworkEntity

        if self._net_entity is None:  # type: ignore
            self._net_entity = self.node.get_or_add_behaviour(NetworkEntity)
        return self._net_entity
