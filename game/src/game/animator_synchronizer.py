from common.behaviours.animator import Animator
from common.behaviours.network_behaviour import NetworkBehaviour
from common.network import DeliveryMode


class AnimatorSynchronizer(NetworkBehaviour):
    def on_init(self):
        self._animator = self.node.get_or_add_behaviour(Animator)
        self._animation = self.use_sync_var(
            str, "null", delivery_mode=DeliveryMode.UNRELIABLE
        )

    def on_server_tick(self, tick_id: int):
        self._animation.value = self._animator.current_animation_name or "null"

    def on_client_tick(self, tick_id: int):
        self._animator.play(self._animation.value)
