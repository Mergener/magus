from __future__ import annotations

from abc import ABC, ABCMeta
from typing import Callable, ClassVar, final

from common.behaviour import Behaviour
from common.behaviours.network_entity import EntityPacket, NetworkEntity
from common.utils import overrides_method


def entity_packet_handler(t):
    def inner(fn):
        fn._packet_type = t  # type: ignore

        def wrapper(self, packet):
            fn(self, packet)

        return wrapper

    return inner


class NetworkBehaviourMeta(ABCMeta):
    def __new__(mcls, name, bases, namespace):
        cls = super().__new__(mcls, name, bases, namespace)

        inherited: dict[type, Callable] = {}
        for base in bases:
            inherited.update(getattr(base, "_packet_handlers", {}))

        own = {
            fn._packet_type: fn
            for fn in namespace.values()
            if hasattr(fn, "_packet_type")
        }

        cls._packet_handlers = {**inherited, **own}  # type: ignore
        return cls


class NetworkBehaviour(Behaviour, ABC, metaclass=NetworkBehaviourMeta):
    _packet_handlers: ClassVar[dict[type, Callable]] = {}

    @property
    def net_entity(self):
        if self._net_entity is None:  # type: ignore
            self._net_entity = self.node.get_or_add_behaviour(NetworkEntity)
        return self._net_entity

    @final
    def on_pre_start(self):
        assert self.game

        parent_on_pre_start = getattr(super(), "on_pre_start", None)
        if callable(parent_on_pre_start):
            parent_on_pre_start()

        for packet_type, handler in self._packet_handlers.items():
            bound = handler.__get__(self, self.__class__)
            self.net_entity.listen(packet_type, bound)

        prev_rcv_updates = self.receive_updates
        self.receive_updates = False
        if self.game.network.is_server():
            self.on_server_pre_start()
            if overrides_method(
                NetworkBehaviour, self, "on_server_update"
            ) or overrides_method(NetworkBehaviour, self, "on_server_tick"):
                self.receive_updates = prev_rcv_updates
        if self.game.network.is_client():
            self.on_client_pre_start()
            if overrides_method(
                NetworkBehaviour, self, "on_client_update"
            ) or overrides_method(NetworkBehaviour, self, "on_client_tick"):
                self.receive_updates = prev_rcv_updates

    @final
    def on_start(self):
        assert self.game
        parent_on_start = getattr(super(), "on_start", None)
        if callable(parent_on_start):
            parent_on_start()

        if self.game.network.is_server():
            self.on_server_start()
        if self.game.network.is_client():
            self.on_client_start()

    @final
    def on_update(self, dt: float):
        assert self.game
        if self.game.network.is_server():
            self.on_server_update(dt)
        if self.game.network.is_client():
            self.on_client_update(dt)

    @final
    def on_tick(self, tick_id: int):
        assert self.game
        if self.game.network.is_server():
            self.on_server_tick(tick_id)
        if self.game.network.is_client():
            self.on_client_tick(tick_id)

    def on_client_pre_start(self):
        pass

    def on_server_pre_start(self):
        pass

    def on_client_start(self):
        pass

    def on_server_start(self):
        pass

    def on_client_update(self, dt: float):
        pass

    def on_server_update(self, dt: float):
        pass

    def on_client_tick(self, tick_id: int):
        pass

    def on_server_tick(self, tick_id: int):
        pass
