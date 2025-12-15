from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from sys import stderr
from typing import Callable, cast

from common.assets import load_node_asset
from common.behaviour import Behaviour
from common.behaviours.network_entity import (
    EntityPacket,
    NetworkEntity,
    PositionUpdate,
    RotationUpdate,
    ScaleUpdate,
)
from common.behaviours.singleton_behaviour import SingletonBehaviour
from common.binary import ByteReader, ByteWriter
from common.network import DeliveryMode, MultiPacket, NetPeer, Packet
from common.node import Node


class NetworkEntityManager(SingletonBehaviour):
    _templates: dict[str, str]
    _entities: dict[int, NetworkEntity]

    def on_init(self):
        self._templates = getattr(self, "_entity_templates", {})
        self._entities = getattr(self, "_entities", {})
        self._next_entity_id = 1

    def on_pre_start(self):
        super().on_pre_start()

        print("Initialized entity manager.")

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
        if self.game.network.is_server():
            self._handle_connection_listener = self.game.network.listen_connected(
                self._handle_connection
            )

    def on_destroy(self):
        assert self.game
        if hasattr(self, "_entity_packet_listener"):
            self.game.network.unlisten(EntityPacket, self._entity_packet_listener)
        if hasattr(self, "_spawn_entity_listener"):
            self.game.network.unlisten(SpawnEntity, self._spawn_entity_listener)
        if hasattr(self, "_destroy_entity_listener"):
            self.game.network.unlisten(DestroyEntity, self._destroy_entity_listener)
        if hasattr(self, "_handle_connection_listener"):
            self.game.network.unlisten_connected(self._handle_connection)

    def spawn_entity(
        self,
        template_id: str | None = None,
        parent: NetworkEntity | None = None,
        include_packets: Callable[[int], list[Packet]] | None = None,
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

        full_packet = MultiPacket(
            [spawn_entity_packet, *entity.generate_sync_packets()],
            DeliveryMode.RELIABLE_ORDERED,
        )

        if include_packets is not None:
            full_packet.packets += include_packets(entity.id)

        self.game.network.publish(full_packet)

        return entity

    def destroy_entity(self, entity: int | NetworkEntity):
        assert self.game

        if isinstance(entity, int):
            found_entity = self.get_entity_by_id(entity)
            if found_entity is None:
                return
            self._do_destroy_entity(found_entity)
        else:
            self._do_destroy_entity(entity)

    def _do_spawn_entity(self, p: SpawnEntity):
        assert self.game
        parent = self.game.scene
        if p.parent_id is not None:
            parent_entity = self._entities.get(p.parent_id)
            if parent_entity is not None:
                parent = parent_entity.node

        if p.template:
            template = self._templates[p.template]
            node = load_node_asset(template)
        else:
            node = Node()
        node.parent = parent
        entity = node.get_or_add_behaviour(NetworkEntity)
        entity._entity_manager = self
        entity._type = p.template

        self._next_entity_id = self._fill_node_ids(p.id, entity.node)

        print(f"Spawned entity {entity.id} of type {entity._type}")

        return entity

    def _fill_node_ids(self, entity_id: int, node: Node) -> int:
        entity = node.get_behaviour(NetworkEntity)
        if entity is not None:
            entity._id = entity_id
            self._entities[entity_id] = entity

        for c in node.children:
            entity_id += 1
            entity_id = self._fill_node_ids(entity_id, c)
        return entity_id

    def _do_destroy_entity(self, entity: NetworkEntity):
        assert self.game

        entity.node.destroy()
        if entity.id in self._entities:
            del self._entities[entity.id]

            if self.game.network.is_server():
                self.game.network.publish(DestroyEntity(entity.id))

    def _handle_entity_packet(self, p: EntityPacket, peer: NetPeer):
        entity = self._entities.get(p.entity_id)
        if entity is None:
            print(
                f"Received {p.__class__.__name__} packet for non-existing entity {p.entity_id}",
                file=stderr,
            )
            return
        entity._handle_entity_packet(p, peer)

    def _handle_spawn_entity(self, p: SpawnEntity):
        self._do_spawn_entity(p)

    def _handle_destroy_entity(self, p: DestroyEntity):
        entity = self.get_entity_by_id(p.id)
        if entity is None:
            return
        self._do_destroy_entity(entity)

    def on_serialize(self, out_dict: dict):
        out_dict["templates"] = self._templates

    def on_deserialize(self, in_dict: dict):
        self._templates = in_dict.get("templates", {})

    def get_entity_by_id(self, entity_id: int):
        return self._entities.get(entity_id)

    def query_entities(self, predicate: Callable[[NetworkEntity], bool]):
        return (e for e in self._entities.values() if predicate(e))

    def _handle_connection(self, peer: NetPeer):
        assert self.game
        packets = []
        for eid, e in self._entities.items():
            parent_id = None
            if e.parent is not None:
                parent_entity = e.parent.get_behaviour(NetworkEntity)
                if parent_entity is not None:
                    parent_id = parent_entity.id

            packets.append(SpawnEntity(eid, e._type, parent_id))
            packets.extend(e.generate_sync_packets())

        peer.send(MultiPacket(packets, DeliveryMode.RELIABLE_ORDERED))


class SpawnEntity(Packet):
    def __init__(self, id: int, template: str | None, parent_id: int | None = None):
        self.id = id
        self.parent_id = parent_id
        self.template = template

    def on_write(self, writer: ByteWriter):
        if self.parent_id:
            writer.write_int32(-self.id)
            writer.write_int32(self.parent_id)
        else:
            writer.write_int32(self.id)

        if self.template is not None:
            writer.write_bool(True)
            writer.write_str(self.template)
        else:
            writer.write_bool(False)

    def on_read(self, reader: ByteReader):
        self.id = reader.read_int32()
        if self.id < 0:
            self.id = -self.id
            self.parent_id = reader.read_int32()
        else:
            self.parent_id = None

        has_template = reader.read_bool()
        if has_template:
            self.template = reader.read_str()
        else:
            self.template = None

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
