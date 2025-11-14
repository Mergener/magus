from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, cast

from common.behaviour import Behaviour
from common.packets import EntityPacket

if TYPE_CHECKING:
    from client.behaviours.network_entity import NetworkEntity


class NetworkBehaviour(Behaviour, ABC):
    _net_entity: NetworkEntity

    def net_entity(self):
        from client.behaviours.network_entity import NetworkEntity

        if self._net_entity is None:
            if self.__class__ == NetworkEntity:
                self._net_entity = cast(NetworkEntity, self)
            else:
                net_entity = self.node.get_behaviour(NetworkEntity)
                if net_entity is None:
                    net_entity = self.node.add_behaviour(NetworkEntity)
                self._net_entity = net_entity
        return self._net_entity
