from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, cast

from common.engine.behaviour import Behaviour
from common.magus.packets import EntityPacket

if TYPE_CHECKING:
    from client.behaviours.network_entity import NetworkEntity


class NetworkBehaviour(Behaviour, ABC):
    def net_entity(self):
        from client.behaviours.network_entity import NetworkEntity

        if self._net_entity is None:
            self._net_entity: NetworkEntity = cast(
                NetworkEntity, self.node.get_behaviour(NetworkEntity)
            )
        return self._net_entity

    @abstractmethod
    def handle_packet(self, packet: EntityPacket):
        pass
