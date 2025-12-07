from typing import Any, Callable, cast


class Container:
    def __init__(self) -> None:
        self._factories: dict[type, Callable[[], Any]] = {}

    def register_factory[T](self, value_type: type[T], factory: Callable[[], T]):
        self._factories[value_type] = factory

    def register_singleton[T](self, value_type: type[T], instance: T):
        self.register_factory(value_type, lambda: instance)

    def unregister(self, value_type: type):
        self._factories.pop(value_type, None)

    def get[T](self, value_type: type[T]):
        return cast(T | None, self._factories.get(value_type, lambda: None)())

    def is_registered(self, value_type: type):
        return value_type in self._factories
