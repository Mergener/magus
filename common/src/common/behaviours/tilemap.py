from contextlib import contextmanager

import numpy as np
import pygame as pg

from common.assets import ImageAsset, load_image_asset
from common.behaviour import Behaviour
from common.behaviours.sprite_renderer import SpriteRenderer


class Tilemap(Behaviour):
    def on_init(self):
        self._sprite_renderer = self.node.get_or_add_behaviour(SpriteRenderer)
        self._tileset: list[ImageAsset] = []
        self._tiles = np.zeros((200, 200), dtype=int)
        self._tile_size: pg.Vector2 = pg.Vector2(32, 32)
        self._editing = False

    @property
    def tileset(self):
        return self._tileset

    @tileset.setter
    def tileset(self, value: list[ImageAsset]):
        self._tileset = value
        self._update_texture()

    @contextmanager
    def edit(self):
        self._editing = True
        try:
            yield
        finally:
            self._editing = False
            self._update_texture()

    def get_tile_at(self, where: tuple[int, int]):
        x, y = where
        h, w = self._tiles.shape

        if 0 <= y < h and 0 <= x < w:
            return int(self._tiles[y, x])
        return None

    def set_tile_at(self, where: tuple[int, int], tile: int):
        x, y = where
        h, w = self._tiles.shape

        if not (0 <= y < h and 0 <= x < w):
            return

        self._tiles[y, x] = tile

        if not self._editing:
            self._update_texture()

    @property
    def tile_size(self):
        return self._tile_size

    @tile_size.setter
    def tile_size(self, value: pg.Vector2):
        self._tile_size = value
        self._update_texture()

    @property
    def dimensions(self) -> tuple[int, int]:
        h, w = self._tiles.shape
        return (w, h)

    @dimensions.setter
    def dimensions(self, value: tuple[int, int]):
        new_w, new_h = value
        old_h, old_w = self._tiles.shape

        new_tiles = np.zeros((new_h, new_w), dtype=int)

        copy_w = min(old_w, new_w)
        copy_h = min(old_h, new_h)

        new_tiles[0:copy_h, 0:copy_w] = self._tiles[0:copy_h, 0:copy_w]

        self._tiles = new_tiles

        if not self._editing:
            self._update_texture()

    def _update_texture(self):
        if self._editing:
            return

        tile_w = int(self._tile_size.x)
        tile_h = int(self._tile_size.y)

        map_w = self._tiles.shape[1] * tile_w
        map_h = self._tiles.shape[0] * tile_h

        texture = pg.Surface((map_w, map_h), pg.SRCALPHA)

        for y in range(self._tiles.shape[0]):
            for x in range(self._tiles.shape[1]):
                tile_index = self._tiles[y, x] - 1

                if tile_index < 0 or tile_index >= len(self._tileset):
                    continue

                tile_asset: ImageAsset = self._tileset[tile_index]
                tile_surface: pg.Surface = tile_asset.pygame_surface

                texture.blit(tile_surface, (x * tile_w, y * tile_h))

        self._sprite_renderer.texture = texture

    def on_serialize(self, out_dict: dict):
        out_dict["dimensions"] = list(self.dimensions)
        out_dict["tiles"] = [int(v) for v in self._tiles.flatten()]
        out_dict["tileset"] = [img.serialize() for img in self._tileset]

    def on_deserialize(self, in_dict: dict):
        with self.edit():
            self.dimensions = tuple(in_dict.get("dimensions", (200, 200)))
            tileset_data = in_dict.get("tileset")
            if tileset_data is not None and len(tileset_data) > 0:
                self._tileset = [
                    ImageAsset(None).deserialize(data) for data in tileset_data
                ]

            tiles_flat = in_dict.get("tiles")
            if tiles_flat is not None:
                expected_size = self._tiles.size
                if len(tiles_flat) != expected_size:
                    raise ValueError(
                        f"Invalid tile count: expected {expected_size}, got {len(tiles_flat)}"
                    )

                self._tiles = np.array(tiles_flat, dtype=int).reshape(self._tiles.shape)
