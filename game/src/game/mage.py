import pygame as pg

from common.behaviours.network_behaviour import NetworkBehaviour, SyncVarType


class Mage(NetworkBehaviour):
    def on_init(self):
        self.health = self.use_sync_var(SyncVarType.INT32, 0)
