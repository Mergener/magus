from common.engine.behaviour import Behaviour


class NetworkIdentity(Behaviour):
    def on_validate(self):
        self._id: int = 0
