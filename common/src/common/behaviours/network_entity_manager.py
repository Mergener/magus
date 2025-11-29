from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from sys import stderr
from typing import Callable, cast

from common.assets import load_node_asset
from common.behaviour import Behaviour
from common.behaviours.network_entity import EntityPacket, NetworkEntity, PositionUpdate
from common.binary import ByteReader, ByteWriter
from common.network import DeliveryMode, NetPeer, Packet
from common.node import Node


class NetworkEntityManager(Behaviour):
    _templates: dict[str, str]
    _entities: dict[int, NetworkEntity]

    def on_init(self):
        self._templates = getattr(self, "_entity_templates", {})
        self._entities = getattr(self, "_entities", {})
        self._next_entity_id = 1

    def on_pre_start(self):
        assert self.game

        self._entity_packet_listener = getattr(
            self,
            "_entity_packet_listener",
            self.game.network.listen(
                EntityPacket, lambda msg, peer: self._handle_entity_packet(msg, peer)
            ),
        )
        if self.game.network.is_client():
            self._spawn_entity_listener = getattr(
                self,
                "_spawn_entity_listener",
                self.game.network.listen(
                    SpawnEntity, lambda msg, _: self._handle_spawn_entity(msg)
                ),
            )
            self._destroy_entity_listener = getattr(
                self,
                "_destroy_entity_listener",
                self.game.network.listen(
                    DestroyEntity, lambda msg, _: self._handle_destroy_entity(msg)
                ),
            )

    def spawn_entity(
        self, template_id: str, parent: NetworkEntity | None = None
    ) -> NetworkEntity:
        assert self.game
        if not self.game.network.is_server():
            raise Exception("Cannot spawn entity if network is not a server.")

        spawn_entity_packet = SpawnEntity(
            self._next_entity_id + 1,
            template_id,
            parent.id if parent is not None else None,
        )
        entity = self._do_spawn_entity(spawn_entity_packet)
        self.game.network.publish(spawn_entity_packet)
        self.game.network.publish(
            PositionUpdate(
                self.game.simulation.tick_id,
                entity.id,
                entity.transform.position.x,
                entity.transform.position.y,
            ),
            override_delivery_mode=DeliveryMode.RELIABLE_ORDERED,
        )
        return entity

    def destroy_entity(self, entity: int | NetworkEntity):
        assert self.game
        if not self.game.network.is_server():
            raise Exception("Cannot destroy entity if network is not a server.")

        if isinstance(entity, NetworkEntity):
            entity = entity.id

        destroy_entity_packet = DestroyEntity(cast(int, entity))
        self._do_destroy_entity(destroy_entity_packet)
        self.game.network.publish(destroy_entity_packet)

    def _do_spawn_entity(self, p: SpawnEntity):
        assert self.game
        parent = self.game.scene
        if p.parent_id is not None:
            parent_entity = self._entities.get(p.parent_id)
            if parent_entity is not None:
                parent = parent_entity.node

        template = self._templates[p.template]
        node = load_node_asset(template)
        node.parent = parent
        entity = node.get_or_add_behaviour(NetworkEntity)
        entity._entity_manager = self

        self._next_entity_id = self._fill_node_ids(p.id, entity.node)

        return entity

    def _fill_node_ids(self, entity_id: int, node: Node) -> int:
        entity = node.get_behaviour(NetworkEntity)
        if entity is not None:
            entity._id = entity_id
            self._entities[entity_id] = entity
            entity_id += 1

        for c in node.children:
            entity_id = self._fill_node_ids(entity_id, c)
        return entity_id

    def _do_destroy_entity(self, p: DestroyEntity):
        entity = self._entities.get(p.id)
        if entity is None:
            print(f"Tried destroying unknown entity {p.id}", file=stderr)
            return

        entity.node.destroy()
        del self._entities[p.id]

    def _handle_entity_packet(self, p: EntityPacket, peer: NetPeer):
        entity = self._entities.get(p.entity_id)
        if entity is None:
            print(
                f"Received {p.__class__.__name__} packet for non-existing entity {p.id}",
                file=stderr,
            )
            return
        entity._handle_entity_packet(p, peer)

    def _handle_spawn_entity(self, p: SpawnEntity):
        self._do_spawn_entity(p)

    def _handle_destroy_entity(self, p: DestroyEntity):
        self._do_destroy_entity(p)

    def on_serialize(self, out_dict: dict):
        out_dict["templates"] = self._templates

    def on_deserialize(self, in_dict: dict):
        self._templates = in_dict.get("templates", {})
        print(f"Loaded net entity templates: {self._templates}")

    def query_entities(self, predicate: Callable[[NetworkEntity], bool]):
        return (e for e in self._entities.values() if predicate(e))


class SpawnEntity(Packet):
    def __init__(self, id: int, template: str, parent_id: int | None = None):
        self.id = id
        self.parent_id = parent_id
        self.template = template

    def on_write(self, writer: ByteWriter):
        if self.parent_id:
            writer.write_int32(-self.id)
            writer.write_int32(self.parent_id)
        else:
            writer.write_int32(self.id)
        writer.write_str(self.template)

    def on_read(self, reader: ByteReader):
        self.id = reader.read_int32()
        if self.id < 0:
            self.id = -self.id
            self.parent_id = reader.read_int32()
        else:
            self.parent_id = None
        self.template = reader.read_str()

    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.RELIABLE_ORDERED


class DestroyEntity(Packet):
    def __init__(self, id: int):
        self.id = id

    def on_write(self, writer: ByteWriter):
        writer.write_int32(self.id)

    def on_read(self, reader: ByteReader):
        self.id = reader.read_int32()

    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.RELIABLE_ORDERED
