from client.behaviours.network_behaviour import NetworkBehaviour
from client.behaviours.network_entity import NetworkEntity
from common.engine.behaviour import Behaviour
from common.engine.node import Node
from common.magus.packets import CreateEntity, DestroyEntity, EntityPacket


class NetworkManager(Behaviour):
    _entities: dict[int, Node]

    def on_start(self):
        assert self.game
        self._entities = {}
        self.game.network.listen(
            CreateEntity,
            lambda msg, _: self.on_create_entity(msg),
        )
        self.game.network.listen(
            DestroyEntity, lambda msg, _: self.on_destroy_entity(msg)
        )

    def get_entity_by_id(self, id: int) -> Node | None:
        return self._entities.get(id)

    def on_create_entity(self, packet: CreateEntity):
        assert self.game
        node = self.game.scene.add_child()
        entity = node.add_behaviour(NetworkEntity)
        entity._id = packet.id
        entity.setup(packet.type_id)

        self._entities[packet.id] = node

    def on_destroy_entity(self, packet: DestroyEntity):
        assert self.game
        del self._entities[packet.id]

    def on_entity_packet(self, packet: EntityPacket):
        entity = self.get_entity_by_id(packet.id)
        if not entity:
            return

        for b in entity.behaviours:
            if not isinstance(b, NetworkBehaviour):
                continue

            b.handle_packet(packet)
