from abc import ABC

from common.behaviour import Behaviour


class SingletonBehaviour(Behaviour, ABC):
    def on_pre_start(self):
        assert self.game
        if self.game.container.is_registered(type(self)):
            self.node.destroy()
            return

        self.game.container.register_singleton(type(self), self)

    def on_destroy(self):
        assert self.game

        if self.game.container.get(type(self)) == self:
            self.game.container.unregister(type(self))
