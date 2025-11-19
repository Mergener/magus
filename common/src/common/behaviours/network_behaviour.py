from __future__ import annotations

import functools
from abc import ABC, ABCMeta
from typing import Callable, ClassVar

from common.behaviour import Behaviour
from common.behaviours.network_entity import NetworkEntity
from common.packets import EntityPacket, PositionUpdate


def entity_packet_handler[T, TPacket: EntityPacket](t: type[TPacket]):
    def inner(fn: Callable[[T, TPacket], None]):
        fn._packet_type = t  # type: ignore

        @functools.wraps(fn)
        def wrapper(self, packet: TPacket):
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

    def on_start(self):
        parent_on_start = getattr(super(), "on_start", None)
        if callable(parent_on_start):
            parent_on_start()

        for packet_type, handler in self._packet_handlers.items():
            bound = handler.__get__(self, self.__class__)
            self.net_entity.listen(packet_type, bound)

    @entity_packet_handler(PositionUpdate)
    def handle_position_update(self, p: PositionUpdate):
        pass
