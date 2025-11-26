from common.behaviours.animator import Animator
from common.behaviours.network_behaviour import NetworkBehaviour


class Mage(NetworkBehaviour):
    def on_init(self):
        self._animator = self.node.get_or_add_behaviour(Animator)
