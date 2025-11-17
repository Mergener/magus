from client.behaviours.entities import NETWORK_ENTITIES_ASSETS
from common.assets import load_node_asset
from common.behaviour import Behaviour
from common.behaviours.network_behaviour import NetworkBehaviour
from common.behaviours.network_entity import NetworkEntity
from common.node import Node
from common.packets import EntityPacket
from game.packets import CreateEntity, DestroyEntity


class NetworkManager(Behaviour):
    _entities: dict[int, Node]

    def on_start(self):
        assert self.game
        self._entities = {}
        self._create_entity_listener = self.game.network.listen(
            CreateEntity,
            lambda msg, _: self.on_create_entity(msg),
        )
        self._destroy_entity_listener = self.game.network.listen(
            DestroyEntity, lambda msg, _: self.on_destroy_entity(msg)
        )
        self._entity_packet_listener = self.game.network.listen(
            EntityPacket, lambda msg, _: self.on_entity_packet(msg)
        )

    def on_destroy(self):
        assert self.game
        self.game.network.unlisten(CreateEntity, self._create_entity_listener)
        self.game.network.unlisten(DestroyEntity, self._destroy_entity_listener)
        self.game.network.unlisten(EntityPacket, self._entity_packet_listener)

    def get_entity_by_id(self, id: int) -> Node | None:
        return self._entities.get(id)

    def on_create_entity(self, packet: CreateEntity):
        assert self.game
        node = load_node_asset(NETWORK_ENTITIES_ASSETS[packet.type_id])
        self.game.scene.add_child(node)
        entity = node.add_behaviour(NetworkEntity)
        entity._id = packet.id

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
