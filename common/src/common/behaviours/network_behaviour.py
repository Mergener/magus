from __future__ import annotations

import functools
from abc import ABC, ABCMeta
from dataclasses import dataclass
from typing import Callable, ClassVar, Generic, TypeVar, final

import pygame as pg

from common.behaviour import Behaviour
from common.behaviours.network_entity import (
    EntityPacket,
    NetworkEntity,
    PlausibleSyncVarType,
)
from common.network import DeliveryMode
from common.utils import overrides_method


def entity_packet_handler(t):
    """
    Marks an instance method from a NetworkBehaviour derived class
    as a handler for a given EntityPacket derived type t, meaning the
    method will be called whenever the entity receives a packet of type t.
    """

    def inner(fn):
        fn._packet_type = t  # type: ignore

        @functools.wraps(fn)
        def wrapper(self, packet, peer):
            fn(self, packet, peer)

        return wrapper

    return inner


def client_method(method):
    """
    Marks an instance method from a NetworkBehaviour derived class
    as a client method, meaning that calls to the method when network.is_client()
    is False will be ignored.
    """

    @functools.wraps(method)
    def inner(self, *args, **kwargs):
        if self.game.network.is_client():
            return method(self, *args, **kwargs)
        return None

    return inner


def server_method(method):
    """
    Marks an instance method from a NetworkBehaviour derived class
    as a server method, meaning that calls to the method when network.is_server()
    is False will be ignored.
    """

    @functools.wraps(method)
    def inner(self, *args, **kwargs):
        if self.game.network.is_server():
            return method(self, *args, **kwargs)
        return None

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
        if getattr(self, "_net_entity", None) is None:  # type: ignore
            self._net_entity = self.node.get_or_add_behaviour(NetworkEntity)
        return self._net_entity

    @property
    def entity_manager(self):
        return self.net_entity.entity_manager

    def use_sync_var[T: PlausibleSyncVarType](
        self,
        type: type[T],
        initial_value: T | None = None,
        delivery_mode=DeliveryMode.RELIABLE,
    ):
        return self.net_entity.use_sync_var(type, initial_value, delivery_mode)

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
        self.on_common_pre_start()
        if self.game.network.is_server():
            self.on_server_pre_start()
            if (
                overrides_method(NetworkBehaviour, self, "on_server_update")
                or overrides_method(NetworkBehaviour, self, "on_server_tick")
                or overrides_method(NetworkBehaviour, self, "on_common_update")
            ):
                self.receive_updates = prev_rcv_updates
        if self.game.network.is_client():
            self.on_client_pre_start()
            if (
                overrides_method(NetworkBehaviour, self, "on_client_update")
                or overrides_method(NetworkBehaviour, self, "on_client_tick")
                or overrides_method(NetworkBehaviour, self, "on_common_tick")
            ):
                self.receive_updates = prev_rcv_updates

    @final
    def on_start(self):
        assert self.game
        parent_on_start = getattr(super(), "on_start", None)
        if callable(parent_on_start):
            parent_on_start()

        self.on_common_start()
        if self.game.network.is_server():
            self.on_server_start()
        if self.game.network.is_client():
            self.on_client_start()

    @final
    def on_update(self, dt: float):
        assert self.game
        self.on_common_update(dt)
        if self.game.network.is_server():
            self.on_server_update(dt)
        if self.game.network.is_client():
            self.on_client_update(dt)

    @final
    def on_tick(self, tick_id: int):
        assert self.game
        self.on_common_tick(tick_id)
        if self.game.network.is_server():
            self.on_server_tick(tick_id)
        if self.game.network.is_client():
            self.on_client_tick(tick_id)

    def on_client_pre_start(self):
        pass

    def on_client_start(self):
        pass

    def on_client_update(self, dt: float):
        pass

    def on_client_tick(self, tick_id: int):
        pass

    def on_server_pre_start(self):
        pass

    def on_server_start(self):
        pass

    def on_server_update(self, dt: float):
        pass

    def on_server_tick(self, tick_id: int):
        pass

    def on_common_pre_start(self):
        pass

    def on_common_start(self):
        pass

    def on_common_update(self, dt: float):
        pass

    def on_common_tick(self, tick_id: int):
        pass
