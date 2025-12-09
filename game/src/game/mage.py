from __future__ import annotations

from struct import pack

import pygame as pg

import server
from common.behaviours.animator import Animator
from common.behaviours.camera import Camera
from common.behaviours.network_behaviour import (
    NetworkBehaviour,
    client_method,
    entity_packet_handler,
    server_method,
)
from common.behaviours.network_entity import EntityPacket, NetworkEntity
from common.behaviours.physics_object import PhysicsObject
from common.binary import ByteReader, ByteWriter
from common.network import DeliveryMode, NetPeer
from common.primitives import Vector2
from common.utils import clamp, notnull
from game.animator_synchronizer import AnimatorSynchronizer
from game.composite_value import CompositeValue
from game.game_manager import GameManager
from game.orders import Order, OrderMessage, OrderTransition
from game.player import Player
from game.spell import SpellInfo, SpellState, get_spell
from game.ui.status_bar import StatusBar


class MoveToOrder(EntityPacket):
    def __init__(self, entity_id: int, where: Vector2, enqueue: bool = False):
        super().__init__(entity_id)
        self.where = where
        self.enqueue = enqueue

    def on_write(self, writer: ByteWriter):
        super().on_write(writer)
        writer.write_float32(self.where.x)
        writer.write_float32(self.where.y)
        writer.write_bool(self.enqueue)

    def on_read(self, reader: ByteReader):
        super().on_read(reader)
        self.where = Vector2(reader.read_float32(), reader.read_float32())
        self.enqueue = reader.read_bool()

    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.RELIABLE_ORDERED


class CastPointTargetSpellOrder(EntityPacket):
    def __init__(self, entity_id: int, spell_entity_id: int, where: Vector2):
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
        self.where = Vector2(reader.read_float32(), reader.read_float32())

    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.RELIABLE_ORDERED


class AddSpell(EntityPacket):
    def __init__(self, mage_entity_id: int, spell_entity_id: int, spell_info_name: str):
        super().__init__(mage_entity_id)
        self.spell_entity_id = spell_entity_id
        self.spell_info_name = spell_info_name

    def on_write(self, writer: ByteWriter):
        super().on_write(writer)
        writer.write_int32(self.spell_entity_id)
        writer.write_str(self.spell_info_name)

    def on_read(self, reader: ByteReader):
        super().on_read(reader)
        self.spell_entity_id = reader.read_int32()
        self.spell_info_name = reader.read_str()

    @property
    def delivery_mode(self) -> DeliveryMode:
        return DeliveryMode.RELIABLE_ORDERED


class Mage(NetworkBehaviour):
    _move_destination: Vector2 | None
    _health_bar: StatusBar | None

    def on_init(self):
        self._animator = self.node.get_behaviour_in_children(Animator)
        if self._animator:
            self._animator.node.get_or_add_behaviour(AnimatorSynchronizer)

        self._physics_object = self.node.get_or_add_behaviour(PhysicsObject)
        self._spells: list[SpellState] = []
        self.speed = CompositeValue(
            self, base=500, delivery_mode=DeliveryMode.UNRELIABLE
        )
        self.owner_index = self.use_sync_var(int)
        self._max_health = self.use_sync_var(float, 500)
        self._health = self.use_sync_var(float, self.max_health)
        self._last_pressed_move_order_target = Vector2(0, 0)
        self._last_sent_move_order_tick = 0
        self._alive = self.use_sync_var(bool, True)
        self._moving = self.use_sync_var(bool, False)
        self._active_order: Order | None = None
        self._stop_order_requested: bool = False
        self._order_queue: list[Order] = []
        self._stunners = self.use_sync_var(int, 0)

        self._health.add_hook(self._handle_health_changed)

    @property
    def animator(self):
        return self._animator

    @property
    def stunned(self):
        return self._stunners.value > 0

    @server_method
    def push_stun(self):
        prev = self._stunners.value
        self._stunners.value += 1

        if prev <= 0 and self._active_order:
            self._active_order.send(OrderMessage.INTERRUPTED)

    @property
    def health(self):
        return self._health.value

    @health.setter
    def health(self, value: float):
        self._health.value = clamp(value, 0, self.max_health)

    @property
    def max_health(self):
        return self._max_health.value

    @max_health.setter
    def max_health(self, value: float):
        self._max_health.value = value

    @property
    def spells(self):
        return (s for s in self._spells)

    @property
    def owner(self) -> Player:
        return notnull(self._game_manager.get_player_by_index(self.owner_index.value))

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
    def cast_spell_at_point(self, spell: SpellState | SpellInfo, where: Vector2):
        if isinstance(spell, SpellInfo):
            spell_state = self.get_spell_state(spell)
            if spell_state is None:
                return
        else:
            spell_state = spell

        if not spell_state.can_cast_on_point_now(where):
            return

        self.issue_order(spell_state.get_point_cast_order(self, where))

    @server_method
    def take_damage(self, amount: float, damage_source: Player | None):
        self.health -= amount

    def get_spell_state(self, spell: SpellInfo):
        for s in self.spells:
            if s.spell == spell:
                return s
        return None

    @server_method
    def stop(self):
        self._order_queue.clear()
        self._stop_order_requested = True

    @server_method
    def issue_order(self, order: Order):
        self._stop_order_requested = True
        self._order_queue = [order]

    @server_method
    def enqueue_order(self, order: Order):
        self._order_queue.append(order)

    @server_method
    def move_to_order(self, destination: Vector2):
        def order() -> Order:
            self._moving.value = True
            reached = False
            while not reached:
                assert self.game
                tick_interval = self.game.simulation.tick_interval
                curr_pos = self.transform.position

                delta = destination - curr_pos
                if delta.x == 0 and delta.y == 0:
                    break

                delta_normalized = delta.normalize()
                if self._animator:
                    self._animator.transform.rotation = Vector2(0, 1).angle_to(
                        delta_normalized
                    )

                motion = delta_normalized * self.speed.current * tick_interval
                if motion.length_squared() > delta.length_squared():
                    motion = delta
                    reached = True

                self._physics_object.move_and_collide(motion)
                response = yield OrderTransition.CONTINUE
                if response != OrderMessage.STEP:
                    break
            self._moving.value = False

        return order()

    @server_method
    def face(self, where: Vector2):
        delta = where - self.transform.position
        if delta.x == 0 and delta.y == 0:
            return

        delta_normalized = delta.normalize()
        if self._animator:
            self._animator.transform.rotation = Vector2(0, 1).angle_to(delta_normalized)

    #
    # Private
    #

    def _get_spell_state_by_entity_id(self, entity_id: int):
        for s in self.spells:
            if s.net_entity.id == entity_id:
                return s
        return None

    def _do_add_spell(self, spell_entity: NetworkEntity, spell_info: SpellInfo):
        spell_state = spell_entity.node.add_behaviour(spell_info.state_behaviour)
        spell_state._spell = spell_info
        spell_state._mage = self
        self._spells.append(spell_state)

    def _has_authority(self, peer: NetPeer):
        order_player = self._game_manager.get_player_by_peer(peer)
        owner = self.owner
        return order_player.index == owner.index

    def _handle_health_changed(self, new: float, prev: float):
        if new == prev:
            return

        if new <= 0:
            self.health = 0
            self._alive.value = False
            if self._animator:
                self._animator.play("die")
                self._animator.enqueue("null")

    @client_method
    def _handle_user_input(self):
        assert self.game
        camera = self.game.container.get(Camera)
        if camera is None:
            return

        mouse_world_pos = camera.screen_to_world_space(self.game.input.mouse_pos)

        just_pressed_right = self.game.input.is_mouse_button_just_pressed(
            pg.BUTTON_RIGHT
        )
        pressed_right = self.game.input.is_mouse_button_pressed(pg.BUTTON_RIGHT)

        if pressed_right or just_pressed_right:
            current_tick = self.game.simulation.tick_id

            if just_pressed_right or (
                pressed_right
                and current_tick != self._last_sent_move_order_tick
                and mouse_world_pos != self._last_pressed_move_order_target
            ):
                self.game.network.publish(
                    MoveToOrder(self.net_entity.id, mouse_world_pos)
                )
                self._last_pressed_move_order_target = mouse_world_pos
                self._last_sent_move_order_tick = current_tick

        if self.game.input.is_mouse_button_just_pressed(pg.BUTTON_LEFT):
            fireball = self.get_spell_state(get_spell("fireball"))
            if fireball is not None:
                self.game.network.publish(
                    CastPointTargetSpellOrder(
                        self.net_entity.id, fireball.net_entity.id, mouse_world_pos
                    )
                )

    @server_method
    def _tick_order(self):
        if not self._alive or self.stunned:
            return

        if self._active_order is not None:
            if self._stop_order_requested:
                self._submit_to_order(OrderMessage.STEP)
                self._submit_to_order(OrderMessage.STOP_REQUESTED)
            else:
                self._submit_to_order(OrderMessage.STEP)
        else:
            if len(self._order_queue) == 0:
                return
            self._active_order = self._order_queue.pop(0)
            self._submit_to_order(None)

        self._stop_order_requested = False

    @server_method
    def _tick_animations(self):
        if not self._animator:
            return

        if not self._alive.value:
            return

        if self._moving.value:
            self._animator.play("move")
        else:
            if self._animator.current_animation_name == "idle":
                return

            self._animator.enqueue("idle")

    def _submit_to_order(self, value: OrderMessage | None):
        if not self._active_order:
            return
        try:
            if value is not None:
                self._active_order.send(value)
            else:
                next(self._active_order)
        except StopIteration:
            self._active_order = None

    #
    # Packet handlers
    #

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

    @entity_packet_handler(AddSpell)
    def _handle_add_spell(self, packet: AddSpell, peer: NetPeer):
        spell_entity = self.entity_manager.get_entity_by_id(packet.spell_entity_id)
        if spell_entity is None:
            return

        spell = get_spell(packet.spell_info_name)
        if spell is None:
            return

        self._do_add_spell(spell_entity, spell)

    @entity_packet_handler(MoveToOrder)
    def _handle_move_to_order(self, packet: MoveToOrder, peer: NetPeer):
        if not self._has_authority(peer):
            return

        order = self.move_to_order(packet.where)
        if packet.enqueue:
            self.enqueue_order(order)
        else:
            self.issue_order(order)

    #
    # Lifecycle
    #

    def on_common_pre_start(self):
        assert self.game
        self._game_manager = notnull(
            self.game.scene.get_behaviour_in_children(GameManager, recursive=True)
        )

    def on_client_start(self):
        self._health_bar = self.node.get_behaviour_in_children(
            StatusBar, include_self=False
        )

    def on_server_start(self):
        assert self.game
        assert self._animator

        spell = get_spell("fireball")
        self.add_spell(spell)

    def on_client_tick(self, tick_id: int):
        health_ratio = self.health / max(1, self.max_health)
        if self._health_bar:
            if health_ratio != self._health_bar.value:
                self._health_bar.value = health_ratio

    def on_server_tick(self, tick_id: int):
        assert self.game

        self._tick_animations()
        self._tick_order()

    def on_client_update(self, dt: float):
        self._handle_user_input()

    def on_serialize(self, out_dict: dict):
        out_dict["speed"] = self.speed.base.value
        out_dict["max_health"] = self.max_health

    def on_deserialize(self, in_dict: dict):
        self.speed.base.value = in_dict.get("speed", 500)
        self.max_health = in_dict.get("max_health", 100)
