from common.behaviours.network_behaviour import NetworkBehaviour
from common.behaviours.network_entity import SyncVar
from common.network import DeliveryMode


class CompositeValue[T: int | float]:
    base: SyncVar[T]
    increment: SyncVar[T]
    multiplier: SyncVar[T]

    def __init__(
        self,
        behaviour: NetworkBehaviour,
        t: type[T] = float,  # type: ignore
        base: T | None = None,
        increment: T | None = None,
        multiplier: T | None = None,
        delivery_mode: DeliveryMode = DeliveryMode.RELIABLE,
    ):
        self.base = behaviour.use_sync_var(
            t, base if base is not None else 0, delivery_mode
        )  # type: ignore
        self.increment = behaviour.use_sync_var(
            t, increment if increment is not None else 0, delivery_mode
        )  # type: ignore
        self.multiplier = behaviour.use_sync_var(
            t, multiplier if multiplier is not None else 1, delivery_mode
        )  # type: ignore

    @property
    def current(self):
        return self.base.value * self.multiplier.value + self.increment.value
