from client.behaviours.network_identity import NetworkIdentity
from common.behaviour import Behaviour
from common.packets import CreateEntity


class NetworkManager(Behaviour):
    _entities: dict[int, NetworkIdentity]

    def on_start(self):
        assert self.game
        self._entities = {}
        self.game.network.listen(
            CreateEntity, lambda msg, _: self.on_create_entity(msg)
        )

    def on_create_entity(self, packet: CreateEntity):
        assert self.game
        self.game.scene.add_child().add_behaviour(NetworkIdentity)._id = packet.id
