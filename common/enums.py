from enum import Enum
import enet

class DeliveryMode(Enum):
    UNRELIABLE = 0
    RELIABLE = 1
    RELIABLE_ORDERED = 2
    
    def to_enet(self) -> tuple[int, int]:
        """
        Returns (channel_id, enet_flags) for sending packets.
        """
        if self is DeliveryMode.UNRELIABLE:
            return 1, enet.PACKET_FLAG_UNSEQUENCED
        if self is DeliveryMode.RELIABLE:
            return 1, enet.PACKET_FLAG_RELIABLE
        if self is DeliveryMode.RELIABLE_ORDERED:
            return 0, enet.PACKET_FLAG_RELIABLE
        raise ValueError(f"Unknown DeliveryMode: {self}")

    @classmethod
    def from_enet(cls, flags: int, channel: int) -> "DeliveryMode":
        """
        Detects the DeliveryMode from ENet flags and channel.
        - channel 0 + RELIABLE → RELIABLE_ORDERED
        - channel 1 + RELIABLE → RELIABLE
        - UNSEQUENCED → UNRELIABLE
        """
        if flags & enet.PACKET_FLAG_UNSEQUENCED:
            return cls.UNRELIABLE
        if flags & enet.PACKET_FLAG_RELIABLE:
            if channel == 0:
                return cls.RELIABLE_ORDERED
            else:
                return cls.RELIABLE
        return cls.UNRELIABLE