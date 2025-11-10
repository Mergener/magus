from common.engine.behaviour import Behaviour
from common.engine.packets import CreateEntity


class NetworkIdentity(Behaviour):
    _id: int

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

        self.game.network.publish(CreateEntity(self._id, parent_id))
