from common.behaviour import Behaviour
from common.packets import CreateEntity
from game.entity_type import EntityType


class NetworkIdentity(Behaviour):
    _id: int
    _type_id: int

    @property
    def id(self):
        return self._id

    def on_start(self):
        assert self.game

        parent_id = None
        if self.parent:
            parent_identity = self.parent.get_behaviour(NetworkIdentity)
            if parent_identity is not None:
                parent_id = parent_identity._id

        self.game.network.publish(CreateEntity(self._id, EntityType.MAGE, parent_id))
