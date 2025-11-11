from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, cast

from common.engine.behaviour import Behaviour
from common.magus.packets import EntityPacket

if TYPE_CHECKING:
    from client.behaviours.network_identity import NetworkIdentity


class NetworkBehaviour(Behaviour, ABC):
    _identity: NetworkIdentity

    def identity(self):
        from client.behaviours.network_identity import NetworkIdentity

        if self._identity is None:
            self._identity = cast(
                NetworkIdentity, self.node.get_behaviour(NetworkIdentity)
            )
        return self._identity

    @abstractmethod
    def handle_packet(self, packet: EntityPacket):
        pass
