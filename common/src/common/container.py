from typing import Any, Callable, cast


class Container:
    def __init__(self) -> None:
        self._singleton_factories: dict[type, Callable[[], Any]] = {}

    def register_factory[T](self, value_type: type[T], factory: Callable[[], T]):
        self._singleton_factories[value_type] = factory

    def register_singleton[T](self, value_type: type[T], instance: T):
        self.register_factory(value_type, lambda: instance)

    def get[T](self, value_type: type[T]):
        return cast(T | None, self._singleton_factories.get(value_type, lambda: None)())
