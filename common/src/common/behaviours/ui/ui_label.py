from enum import Enum
from sys import stderr

import pygame as pg

from common.assets import load_font_asset
from common.behaviours.ui.ui_surface import UISurface
from common.behaviours.ui.widget import Widget
from common.primitives import Vector2


class HorizontalAlign(Enum):
    LEFT = 0
    CENTER = 1
    RIGHT = 2


class VerticalAlign(Enum):
    TOP = 0
    MIDDLE = 1
    BOTTOM = 2


class UILabel(Widget):
    def on_init(self):
        super().on_init()

        self._texture_node = self.node.add_child()
        self._ui_texture: UISurface = self._texture_node.add_behaviour(UISurface)

        self._text: str = ""
        self._font_name: str | None = None
        self._font_size: int = 24
        self._bold: bool = False
        self._italic: bool = False
        self._color: pg.Color = pg.Color(255, 255, 255, 255)
        self._anti_alias: bool = True
        self._horizontal_align: HorizontalAlign = HorizontalAlign.CENTER
        self._vertical_align: VerticalAlign = VerticalAlign.MIDDLE

    def on_start(self):
        self._refresh_text_surface()

    def _refresh_text_surface(self):
        if not self._text:
            self._ui_texture.set_surface(None)
            return

        lines = self._text.split("\n")
        if len(lines) == 0:
            self._ui_texture.set_surface(None)
            return

        try:

            # Quick hack:
            # Since our text will scale with screen size, a little trick to maintain quality
            # is to render the texture in a larger font size and scale that down, instead
            # of upscaling smaller texts and losing quality.
            FONT_FACTOR = 10

            line_padding = self._font_size // 10

            font = load_font_asset(
                self._font_name or "Arial",
                self._font_size * FONT_FACTOR,
                self._bold,
                self._italic,
            )

            surfaces: list[pg.Surface] = []

            width = 0
            for line in lines:
                s = font.render(line, self._anti_alias, self._color)
                surfaces.append(s)
                width = max(width, s.get_width())

            height = (surfaces[0].get_height() + line_padding) * len(surfaces)
            surface = pg.Surface((width, height), pg.SRCALPHA).convert_alpha()
            for i, s in enumerate(surfaces):
                y = i * (height // len(surfaces))

                w_diff = width - s.get_width()

                if self.horizontal_align == HorizontalAlign.CENTER:
                    x = w_diff / 2
                elif self.horizontal_align == HorizontalAlign.LEFT:
                    x = 0
                else:  # Right
                    x = w_diff

                surface.blit(s, pg.Rect((x, y), (width, height)))

            self._update_alignment()
            self._ui_texture.surface_scale = Vector2(1 / FONT_FACTOR, 1 / FONT_FACTOR)
            self._ui_texture.set_surface(surface)

        except Exception as e:
            print(f"Failed to render text: {e}")
            self._ui_texture.set_surface(None)

    def _update_alignment(self):
        transformed_surface = self._ui_texture.transformed_surface
        if transformed_surface is None:
            return

        text_width = transformed_surface.get_width()
        text_height = transformed_surface.get_height()

        if self._horizontal_align == HorizontalAlign.LEFT:
            offset_x = 0
        elif self._horizontal_align == HorizontalAlign.CENTER:
            offset_x = -text_width / 2
        else:
            offset_x = -text_width

        if self._vertical_align == VerticalAlign.TOP:
            offset_y = 0
        elif self._vertical_align == VerticalAlign.MIDDLE:
            offset_y = -text_height / 2
        else:
            offset_y = -text_height

        self._ui_texture.transform.position = Vector2(offset_x, offset_y)

    @property
    def anchor(self):
        return self._ui_texture.anchor

    @anchor.setter
    def anchor(self, value: Vector2):
        self._ui_texture.anchor = value

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value: str):
        self._text = value.replace("\\n", "\n")
        self._refresh_text_surface()

    @property
    def font_name(self):
        return self._font_name

    @font_name.setter
    def font_name(self, value: str | None):
        self._font_name = value
        self._refresh_text_surface()

    @property
    def font_size(self):
        return self._font_size

    @font_size.setter
    def font_size(self, value: int):
        self._font_size = max(1, value)
        self._refresh_text_surface()

    @property
    def bold(self):
        return self._bold

    @bold.setter
    def bold(self, value: bool):
        self._bold = value
        self._refresh_text_surface()

    @property
    def italic(self):
        return self._italic

    @italic.setter
    def italic(self, value: bool):
        self._italic = value
        self._refresh_text_surface()

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value: pg.Color | tuple):
        if isinstance(value, tuple):
            self._color = pg.Color(*value)
        else:
            self._color = value
        self._refresh_text_surface()

    @property
    def anti_alias(self):
        return self._anti_alias

    @anti_alias.setter
    def anti_alias(self, value: bool):
        self._anti_alias = value
        self._refresh_text_surface()

    @property
    def horizontal_align(self):
        return self._horizontal_align

    @horizontal_align.setter
    def horizontal_align(self, value: HorizontalAlign):
        self._horizontal_align = value
        self._update_alignment()

    @property
    def vertical_align(self):
        return self._vertical_align

    @vertical_align.setter
    def vertical_align(self, value: VerticalAlign):
        self._vertical_align = value
        self._update_alignment()

    @property
    def tint(self):
        """Expose tint property from underlying texture base"""
        return self._ui_texture.tint

    @tint.setter
    def tint(self, value: pg.Color | tuple):
        """Set tint on underlying texture base"""
        self._ui_texture.tint = value

    def on_serialize(self, out_dict: dict):
        super().on_serialize(out_dict)
        out_dict["text"] = self._text
        out_dict["font_name"] = self._font_name
        out_dict["font_size"] = self._font_size
        out_dict["bold"] = self._bold
        out_dict["italic"] = self._italic
        out_dict["color"] = {
            "r": self._color.r,
            "g": self._color.g,
            "b": self._color.b,
            "a": self._color.a,
        }
        out_dict["anti_alias"] = self._anti_alias
        out_dict["horizontal_align"] = self._horizontal_align.name.lower()
        out_dict["vertical_align"] = self._vertical_align.name.lower()

    def on_deserialize(self, in_dict: dict):
        super().on_deserialize(in_dict)
        self._text = in_dict.get("text", "")
        self._font_name = in_dict.get("font_name", None)
        self._font_size = in_dict.get("font_size", 24)
        self._bold = in_dict.get("bold", False)
        self._italic = in_dict.get("italic", False)

        color_dict = in_dict.get("color")
        if color_dict:
            self._color = pg.Color(
                color_dict.get("r", 255),
                color_dict.get("g", 255),
                color_dict.get("b", 255),
                color_dict.get("a", 255),
            )
        else:
            self._color = pg.Color(255, 255, 255, 255)

        self._anti_alias = in_dict.get("anti_alias", True)

        h_align_name = in_dict.get("horizontal_align", "left").upper()
        try:
            self._horizontal_align = HorizontalAlign[h_align_name]
        except KeyError:
            print(f"Invalid horizontal align {h_align_name}", file=stderr)
            self._horizontal_align = HorizontalAlign.LEFT

        v_align_name = in_dict.get("vertical_align", "top").upper()
        try:
            self._vertical_align = VerticalAlign[v_align_name]
        except KeyError:
            print(f"Invalid vertical align {v_align_name}", file=stderr)
            self._vertical_align = VerticalAlign.TOP

        self._refresh_text_surface()

    @property
    def rect(self):
        return self._ui_texture.rect
