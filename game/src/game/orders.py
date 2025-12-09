from abc import ABC
from enum import Enum
from typing import Generator


class OrderMessage(Enum):
    STEP = 0
    STOP_REQUESTED = 1
    INTERRUPTED = 2


class OrderTransition(Enum):
    CONTINUE = 0


Order = Generator[OrderTransition, OrderMessage, None]
