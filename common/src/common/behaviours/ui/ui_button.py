from typing import Any, Callable

import pygame as pg

from common.behaviours.ui.ui_image import UIImage
from common.behaviours.ui.ui_label import UILabel
from common.behaviours.ui.widget import Widget
from common.primitives import Vector2


class UIButton(Widget):
    def on_init(self):
        super().on_init()

        self._ui_image = self.node.get_or_add_behaviour(UIImage)
        self._ui_label = self.node.get_or_add_behaviour(UILabel)

        self._normal_color: pg.Color = pg.Color(255, 255, 255, 255)
        self._hovered_color: pg.Color = pg.Color(220, 220, 220, 255)
        self._pressed_color: pg.Color = pg.Color(180, 180, 180, 255)

        self._is_hovered: bool = False
        self._is_pressed: bool = False
        self._was_pressed_inside: bool = False

        self.on_click: Callable[[], Any] | None = None
        self._update_colors()

    def _update_colors(self):
        if self._is_pressed:
            color = self._pressed_color
        elif self._is_hovered:
            color = self._hovered_color
        else:
            color = self._normal_color

        self._ui_image.tint_color = color

    def _is_mouse_over_button(self):
        assert self.game

        canvas = self.canvas
        if canvas is None:
            return False

        mouse_pos = canvas.screen_to_canvas_point(Vector2(self.game.input.mouse_pos))

        if self._ui_image.transformed_surface is not None:
            hovering = self.rect.collidepoint(mouse_pos.x, mouse_pos.y)
            return hovering

        return False

    def on_update(self, dt: float):
        assert self.game

        if self._ui_image.render_layer != self.render_layer - 1:
            self._ui_image.render_layer = self.render_layer - 1

        game_input = self.game.input

        was_pressed = self._is_pressed
        was_hovered = self._is_hovered
        self._is_hovered = self._is_mouse_over_button()

        if game_input.is_mouse_button_just_pressed(pg.BUTTON_LEFT):
            if self._is_hovered:
                self._is_pressed = True
                self._was_pressed_inside = True

        if game_input.is_mouse_button_just_released(pg.BUTTON_LEFT):
            if self._is_pressed and self._is_hovered and self._was_pressed_inside:
                if self.on_click is not None:
                    self.game.simulation.run_task(self.on_click())

            self._is_pressed = False
            self._was_pressed_inside = False

        if self._is_pressed and not game_input.is_mouse_button_pressed(pg.BUTTON_LEFT):
            self._is_pressed = False
            self._was_pressed_inside = False

        if was_hovered != self._is_hovered or self._is_pressed != was_pressed:
            self._update_colors()

    @property
    def image(self):
        return self._ui_image

    @property
    def label(self):
        return self._ui_label

    @property
    def normal_color(self):
        return self._normal_color

    @normal_color.setter
    def normal_color(self, value: pg.Color | tuple):
        if isinstance(value, tuple):
            self._normal_color = pg.Color(*value)
        else:
            self._normal_color = value
        self._update_colors()

    @property
    def hovered_color(self):
        return self._hovered_color

    @hovered_color.setter
    def hovered_color(self, value: pg.Color | tuple):
        if isinstance(value, tuple):
            self._hovered_color = pg.Color(*value)
        else:
            self._hovered_color = value
        self._update_colors()

    @property
    def pressed_color(self):
        return self._pressed_color

    @pressed_color.setter
    def pressed_color(self, value: pg.Color | tuple):
        if isinstance(value, tuple):
            self._pressed_color = pg.Color(*value)
        else:
            self._pressed_color = value
        self._update_colors()

    @property
    def rect(self):
        return self._ui_image.rect

    def on_serialize(self, out_dict: dict):
        super().on_serialize(out_dict)
        out_dict["normal_color"] = {
            "r": self._normal_color.r,
            "g": self._normal_color.g,
            "b": self._normal_color.b,
            "a": self._normal_color.a,
        }
        out_dict["hovered_color"] = {
            "r": self._hovered_color.r,
            "g": self._hovered_color.g,
            "b": self._hovered_color.b,
            "a": self._hovered_color.a,
        }
        out_dict["pressed_color"] = {
            "r": self._pressed_color.r,
            "g": self._pressed_color.g,
            "b": self._pressed_color.b,
            "a": self._pressed_color.a,
        }

    def on_deserialize(self, in_dict: dict):
        super().on_deserialize(in_dict)

        def deserialize_color(color_dict, default):
            if color_dict:
                return pg.Color(
                    color_dict.get("r", 255),
                    color_dict.get("g", 255),
                    color_dict.get("b", 255),
                    color_dict.get("a", 255),
                )
            return default

        self._normal_color = deserialize_color(
            in_dict.get("normal_color"), pg.Color(255, 255, 255, 255)
        )
        self._hovered_color = deserialize_color(
            in_dict.get("hovered_color"), pg.Color(220, 220, 220, 255)
        )
        self._pressed_color = deserialize_color(
            in_dict.get("pressed_color"), pg.Color(180, 180, 180, 255)
        )

        self._update_colors()
