import pygame as pg

from client.behaviours.camera import Camera
from common.simulation import Behaviour


class SpriteRenderer(Behaviour):
    _dimensions: pg.Vector2 | None
    def __init__(self, texture: pg.Surface | None = None):
        super().__init__()

        self.texture = texture
        
    @property
    def texture(self):
        return self._texture

    @texture.setter
    def texture(self, texture: pg.Surface | None):
        self._texture = texture

        if texture is not None:
            self._dimensions = pg.Vector2(texture.get_width(), texture.get_height())
        else:
            self._dimensions = None

    def on_render(self):
        if self.texture is None:
            return

        camera = Camera.main
        if camera is None:
            return

        dim = self._dimensions * self.transform.scale
        pos = camera.screen_to_world_space(self.transform.position - dim / 2)
        draw_rect = pg.Rect(pos, dim)
        window = pg.display.get_surface()
        if not draw_rect.colliderect(window.get_rect()):
            # Object not visible.
            return

        window.blit(self.texture, draw_rect)
