from abc import ABC

from common.behaviours.network_behaviour import NetworkBehaviour


class Projectile(NetworkBehaviour, ABC):
    def on_init(self):
        self.speed = self.use_sync_var(float)
