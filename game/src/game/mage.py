import pygame as pg

from common.behaviours.animator import Animator
from common.behaviours.camera import Camera
from common.behaviours.network_behaviour import NetworkBehaviour, entity_packet_handler
from common.behaviours.network_entity import EntityPacket
from common.behaviours.physics_object import PhysicsObject
from common.binary import ByteReader, ByteWriter
from common.network import DeliveryMode, NetPeer
from common.utils import notnull
from game.game_manager import GameManager
from game.player import Player


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


class Mage(NetworkBehaviour):
    _move_destination: pg.Vector2 | None

    def on_init(self):
        self._animator = self.node.get_or_add_behaviour(Animator)
        self._physics_object = self.node.get_or_add_behaviour(PhysicsObject)
        self._move_destination = None
        self.speed = self.use_sync_var(float, 500)
        self.owner_index = self.use_sync_var(int)

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
        self.speed.value -= 5 * tick_interval

        if self._move_destination is None:
            return

        delta = self._move_destination - self.transform.position
        if delta.x == 0 and delta.y == 0:
            return

        motion = delta.normalize() * self.speed.value * tick_interval
        if motion.length_squared() > delta.length_squared():
            motion = delta
            self._move_destination = None

        self._physics_object.move_and_collide(motion)

    @property
    def owner(self) -> Player:
        return notnull(self._game_manager.get_player_by_index(self.owner_index.value))

    @entity_packet_handler(MoveToOrder)
    def _handle_move_to_order(self, order: MoveToOrder, peer: NetPeer):
        order_player = self._game_manager.get_player_by_peer(peer)
        owner = self.owner
        if order_player.index != owner.index:
            return

        self._move_destination = order.where
