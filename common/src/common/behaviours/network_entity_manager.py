from sys import stderr
from typing import cast

from common.assets import load_node_asset
from common.behaviour import Behaviour
from common.behaviours.network_entity import NetworkEntity
from common.node import Node
from common.packets import CreateEntity, DestroyEntity, EntityPacket


class NetworkEntityManager(Behaviour):
    _templates: list[str]
    _entities: dict[int, NetworkEntity]

    def on_init(self):
        assert self.game

        self._templates = getattr(self, "_entity_templates", [])
        self._entities = getattr(self, "_entities", {})
        self._entity_packet_listener = getattr(
            self,
            "_entity_packet_listener",
            self.game.network.listen(
                EntityPacket, lambda msg, _: self.on_entity_packet(msg)
            ),
        )
        self._create_entity_listener = getattr(
            self,
            "_create_entity_listener",
            self.game.network.listen(
                CreateEntity, lambda msg, _: self.on_create_entity(msg)
            ),
        )
        self._destroy_entity_listener = getattr(
            self,
            "_destroy_entity_listener",
            self.game.network.listen(
                DestroyEntity, lambda msg, _: self.on_destroy_entity(msg)
            ),
        )

    def on_entity_packet(self, p: EntityPacket):
        entity = self._entities.get(p.id)
        if entity is None:
            print(
                f"Received {p.__class__.__name__} packet for non-existing entity {p.id}",
                file=stderr,
            )
            return
        entity._handle_entity_packet(p)

    def on_create_entity(self, p: CreateEntity):
        assert self.game

        parent = self.game.scene
        if p.parent_id is not None:
            parent_entity = self._entities.get(p.parent_id)
            if parent_entity is not None:
                parent = parent_entity.node

        if p.template_id in range(len(self._templates)):
            node = load_node_asset(self._templates[p.template_id])
            node.parent = parent
            entity = node.get_or_add_behaviour(NetworkEntity)
        else:
            print(f"Couldn't find template ID {p.template_id}", file=stderr)
            entity = parent.add_child().add_behaviour(NetworkEntity)

        entity._id = p.id
        self._entities[p.id] = entity

    def on_destroy_entity(self, p: DestroyEntity):
        entity = self._entities.get(p.id)
        if entity is None:
            print(f"Tried destroying unknown entity {p.id}", file=stderr)
            return

        entity.node.destroy()
        del self._entities[p.id]

    def on_serialize(self, out_dict: dict):
        out_dict["templates"] = self._templates

    def on_deserialize(self, in_dict: dict):
        self._templates = in_dict.get("templates", [])
