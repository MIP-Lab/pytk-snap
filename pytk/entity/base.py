import vedo
import vedo.vtkclasses as vtki
import numpy as np
from vedo import colors

class Text3D(vedo.Text3D):
    
    def opacity(self, *argv):
        return super().opacity()

class Image2D(vedo.Image):
    
    def opacity(self, value=None):
        if value is not None:
            self.actor.SetOpacity(value)
        return self.actor.GetOpacity()

    def shift(self, x, y, z):
        position = self.pos()
        self.pos(position[0] + x, position[1] + y, position[2] + z)

    def pos(self, x=None, y=None, z=None):
        if x is not None:
            self.actor.SetPosition(x, y, z)
        return self.actor.GetPosition()

class Entity:

    def __init__(self, name, layer=1, opacity=1) -> None:
        self.name = name
        self.default_opacity = opacity
        self.opacity = opacity
        self.layer=layer
        self.icon = True
        box = vedo.Box(length=0.3, width=0.05, height=0.1, c='#41ab5d')  
        text = Text3D(self.name, s=0.025, c='white', justify='center', font='Ubuntu')
        box.view_name = f'{self.name}_icon'
        text.view_name = f'{self.name}_icon_text'
        self.icon_box = box
        self.icon_text = text
        self.shift_at_render=True
    
    def finish_loading(self):
        pass

    def reset_opacity(self):
        self.opacity = self.opacity
    
    def create_renderables(self, view):
        return []
