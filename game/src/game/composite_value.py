from common.behaviours.network_behaviour import NetworkBehaviour
from common.network import DeliveryMode


class CompositeValue[T: int | float]:
    def __init__(
        self,
        behaviour: NetworkBehaviour,
        t: type[T] = float,
        base: T | None = None,
        increment: T | None = None,
        multiplier: T | None = None,
        delivery_mode: DeliveryMode = DeliveryMode.RELIABLE,
    ):
        self.base = behaviour.use_sync_var(
            t, base if base is not None else 0, delivery_mode
        )
        self.increment = behaviour.use_sync_var(
            t, increment if increment is not None else 0, delivery_mode
        )
        self.multiplier = behaviour.use_sync_var(
            t, multiplier if multiplier is not None else 1, delivery_mode
        )

    @property
    def current(self):
        return self.base.value * self.multiplier.value + self.increment.value
