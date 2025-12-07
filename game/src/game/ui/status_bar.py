import pygame as pg

from common.behaviour import Behaviour
from common.behaviours.sprite_renderer import SpriteRenderer
from common.primitives import Color, Vector2


class StatusBar(Behaviour):
    def on_init(self):
        self._value: float = 0
        self._filling_texture: pg.Surface | None = None
        self._empty_texture: pg.Surface | None = None
        self.filled_color = Color(0, 255, 0)
        self.empty_color = Color(20, 20, 20)
        self.image_scale = Vector2(1, 1)
        self._filling_sprite: SpriteRenderer | None = None
        self._empty_sprite: SpriteRenderer | None = None

    def on_pre_start(self):
        assert self.game

        fill_texture = self._filling_texture or _generate_simple_rect_texture(
            self.filled_color, Vector2(5, 5)
        )
        self._filling_sprite = self.node.add_child().add_behaviour(SpriteRenderer)
        self._filling_sprite.texture = fill_texture
        self._filling_sprite.image_scale = self.image_scale
        self._filling_sprite.render_layer = self.render_layer + 1

        empty_texture = self._empty_texture or _generate_simple_rect_texture(
            self.empty_color, Vector2(5, 5)
        )
        self._empty_sprite = self.node.add_child().add_behaviour(SpriteRenderer)
        self._empty_sprite.texture = empty_texture
        self._empty_sprite.image_scale = self.image_scale
        self._empty_sprite.render_layer = self.render_layer

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value == self._value:
            return
        self._value = value
        if self._filling_sprite:
            scale = Vector2(max(0, self.image_scale.x * value), self.image_scale.y)
            self._filling_sprite.image_scale = scale

            # If we just resize the filling bar, it will stay centered.
            if self._filling_sprite.texture:
                self._filling_sprite.transform.local_position = Vector2(
                    self._filling_sprite.texture.get_size()
                ).elementwise() * Vector2(scale.x / 2, 0)

    def on_serialize(self, out_dict: dict):
        out_dict["value"] = self.value
        out_dict["filled_color"] = self.filled_color.serialize()
        out_dict["empty_color"] = self.empty_color.serialize()
        out_dict["image_scale"] = self.image_scale.serialize()

    def on_deserialize(self, in_dict: dict):
        self.value = in_dict.get("value", 1)
        self.filled_color.deserialize(in_dict.get("filled_color"))
        self.empty_color.deserialize(in_dict.get("empty_color"))
        self.image_scale.deserialize(in_dict.get("image_scale"))


def _generate_simple_rect_texture(color: Color, size: Vector2):
    texture = pg.Surface(size, pg.SRCALPHA)
    texture.fill(color)
    return texture
