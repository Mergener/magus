import pygame as pg

from common.simulation import Behaviour

class SpriteRenderer(Behaviour):
    def __init__(self, texture: pg.Surface | None = None):
        super().__init__()
        
        self.texture = texture
            
    @property
    def texture(self):
        return self._texture
    
    @texture.setter
    def texture(self, texture: pg.Surface):
        self._texture = texture
        
        if texture is not None:
            self._dimensions = pg.Vector2(texture.get_width(), texture.get_height())
        else:
            self._dimensions = pg.Vector2(100, 100)
            
    def on_render(self, window: pg.Surface):
        if self.texture is None:
            return
        
        draw_rect = pg.Rect(self.transform.position - self._dimensions / 2, self._dimensions)
        window.blit(self.texture, draw_rect)
