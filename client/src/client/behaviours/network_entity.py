from common.engine.behaviour import Behaviour


class NetworkEntity(Behaviour):
    def on_init(self):
        self._id: int = 0
