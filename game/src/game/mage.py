from __future__ import annotations

import pygame as pg

from common.behaviours.animator import Animator
from common.behaviours.camera import Camera
from common.behaviours.network_behaviour import (
    NetworkBehaviour,
    entity_packet_handler,
    server_method,
)
from common.behaviours.network_entity import EntityPacket, NetworkEntity
from common.binary import ByteReader, ByteWriter
from common.network import DeliveryMode, NetPeer
from common.utils import notnull
from game.composite_value import CompositeValue
from game.game_manager import GameManager
from game.player import Player
from game.spell import SpellInfo, SpellState, get_spell


class MoveToOrder(EntityPacket):
    def __init__(self, entity_id: int, where: pg.Vector2):
        super().__init__(entity_id)
        self.where = where

    def on_write(self, writer: ByteWriter):
        super().on_write(writer)
        writer.write_float32(self.where.x)
        writer.write_float32(self.where.y)

    def on_read(self, reader: ByteReader):
        super().on_read(reader)
        self.where = pg.Vector2(reader.read_float32(), reader.read_float32())

    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.RELIABLE_ORDERED


class CastPointTargetSpellOrder(EntityPacket):
    def __init__(self, entity_id: int, spell_entity_id: int, where: pg.Vector2):
        super().__init__(entity_id)
        self.spell_entity_id = spell_entity_id
        self.where = where

    def on_write(self, writer: ByteWriter):
        super().on_write(writer)
        writer.write_int32(self.spell_entity_id)
        writer.write_float32(self.where.x)
        writer.write_float32(self.where.y)

    def on_read(self, reader: ByteReader):
        super().on_read(reader)
        self.spell_entity_id = reader.read_int32()
        self.where = pg.Vector2(reader.read_float32(), reader.read_float32())

    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.RELIABLE_ORDERED


class AddSpell(EntityPacket):
    def __init__(self, mage_entity_id: int, spell_entity_id: int, spell_info_name: str):
        super().__init__(mage_entity_id)
        self.spell_entity_id = spell_entity_id
        self.spell_state_behaviour = spell_info_name

    def on_write(self, writer: ByteWriter):
        super().on_write(writer)
        writer.write_int32(self.spell_entity_id)
        writer.write_str(self.spell_file_name)

    def on_read(self, reader: ByteReader):
        super().on_read(reader)
        self.spell_entity_id = reader.read_int32()
        self.spell_file_name = reader.read_str()

    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.RELIABLE


class Mage(NetworkBehaviour):
    _move_destination: pg.Vector2 | None

    def on_init(self):
        self._animator = self.node.get_or_add_behaviour(Animator)
        self._move_destination = None
        self._spells: list[SpellState] = []
        self.speed = CompositeValue(self, base=500)
        self.owner_index = self.use_sync_var(int)

    @property
    def spells(self):
        return (s for s in self._spells)

    def on_common_pre_start(self):
        assert self.game
        self._game_manager = notnull(
            self.game.scene.get_behaviour_in_children(GameManager)
        )

    def on_client_update(self, dt: float):
        assert self.game
        if self.game.input.is_mouse_button_just_pressed(pg.BUTTON_RIGHT):
            mouse_pos = self.game.input.mouse_pos
            if Camera.main:
                self.game.network.publish(
                    MoveToOrder(
                        self.net_entity.id, Camera.main.screen_to_world_space(mouse_pos)
                    )
                )

    def on_server_tick(self, tick_id: int):
        assert self.game

        tick_interval = self.game.simulation.tick_interval
        self.speed.increment.value -= 5 * tick_interval

        if self._move_destination is None:
            return

        delta = self._move_destination - self.transform.position
        if delta.x == 0 and delta.y == 0:
            return

        motion = delta.normalize() * self.speed.current * tick_interval
        if motion.length_squared() > delta.length_squared():
            motion = delta
            self._move_destination = None

        self.transform.local_position += motion

    @property
    def owner(self) -> Player:
        return notnull(self._game_manager.get_player_by_index(self.owner_index.value))

    @entity_packet_handler(MoveToOrder)
    def _handle_move_to_order(self, order: MoveToOrder, peer: NetPeer):
        if not self._has_authority(peer):
            return

        self._move_destination = order.where

    def on_serialize(self, out_dict: dict):
        out_dict["speed"] = self.speed.base

    def on_deserialize(self, in_dict: dict):
        self.speed.base = in_dict.get("speed", 500)

    def get_spell_state(self, spell: SpellInfo):
        for s in self.spells:
            if s.spell == spell:
                return s
        return None

    def _get_spell_state_by_entity_id(self, entity_id: int):
        for s in self.spells:
            if s.net_entity.id == entity_id:
                return s
        return None

    @server_method
    def add_spell(self, spell: SpellInfo):
        assert self.game

        entity_mgr = self.entity_manager
        spell_entity = entity_mgr.spawn_entity(
            parent=self.net_entity,
            include_packets=lambda spell_id: [
                AddSpell(self.net_entity.id, spell_id, spell.file_name)
            ],
        )
        self._do_add_spell(spell_entity, spell)

    @server_method
    def cast_spell_at_point(self, spell: SpellState | SpellInfo, where: pg.Vector2):
        if isinstance(spell, SpellInfo):
            spell_state = self.get_spell_state(spell)
            if spell_state is None:
                return
        else:
            spell_state = spell

        if not spell_state.can_cast_on_point_now(where):
            return

        spell_state.on_point_cast(where)

    @entity_packet_handler(AddSpell)
    def _handle_add_spell(self, packet: AddSpell, peer: NetPeer):
        spell_entity = self.entity_manager.get_entity_by_id(packet.spell_entity_id)
        if spell_entity is None:
            return

        spell = get_spell(packet.spell_file_name)
        if spell is None:
            return

        self._do_add_spell(spell_entity, spell)

    def _do_add_spell(self, spell_entity: NetworkEntity, spell_info: SpellInfo):
        spell_state = spell_entity.node.add_behaviour(spell_info.state_behaviour)
        spell_state._spell = spell_info
        self._spells.append(spell_state)

    @entity_packet_handler(CastPointTargetSpellOrder)
    def _handle_cast_point_target_spell_order(
        self, order: CastPointTargetSpellOrder, peer: NetPeer
    ):
        if not self._has_authority(peer):
            return

        spell_state = self._get_spell_state_by_entity_id(order.spell_entity_id)
        if not spell_state:
            return

        self.cast_spell_at_point(spell_state, order.where)

    def _has_authority(self, peer: NetPeer):
        order_player = self._game_manager.get_player_by_peer(peer)
        owner = self.owner
        return order_player.index == owner.index
