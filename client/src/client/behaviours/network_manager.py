from client.behaviours.network_identity import NetworkIdentity
from common.engine.behaviour import Behaviour
from common.engine.node import Node
from common.magus.packets import CreateEntity, DestroyEntity


class NetworkManager(Behaviour):
    _entities: dict[int, Node]

    def on_start(self):
        assert self.game
        self._entities = {}
        self.game.network.listen(
            CreateEntity, lambda msg, _: self.on_create_entity(msg)
        )

    def on_create_entity(self, packet: CreateEntity):
        assert self.game
        entity = self.game.scene.add_child()
        entity.add_behaviour(NetworkIdentity)._id = packet.id
        self._entities[packet.id] = entity

    def on_destroy_entity(self, packet: DestroyEntity):
        assert self.game
        del self._entities[packet.id]

    def get_entity_by_id(self, id: int) -> Node | None:
        return self._entities.get(id)
