from abc import ABC
from enum import Enum
from typing import Generator


class OrderMessage(Enum):
    CONTINUE = 0
    STOP_REQUESTED = 1
    INTERRUPTED = 2


class OrderTransition(Enum):
    CONTINUE = 1
    DONE = 2


OrderGenerator = Generator[OrderTransition, OrderMessage, None]
