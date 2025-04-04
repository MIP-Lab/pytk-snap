import numpy as np
import vedo
import vedo.colors
from .base import Entity
from ..view import View2D, View3D

class CrossHair(Entity):
    
    def __init__(self, world_size) -> None:
        super().__init__('crosshair', 10, opacity=1)
        
        crosshair1 = vedo.DashedLine([0, 0, 0], [world_size[0], 0, 0], spacing=0.1, lw=1, c='blue')
        crosshair2 = vedo.DashedLine([0, 0, 0], [0, world_size[1], 0], spacing=0.1, lw=1, c='red')
        crosshair3 = vedo.DashedLine([0, 0, 0], [0, 0, world_size[2]], spacing=0.1, lw=1, c='yellow')
        
        crosshair1.actor.PickableOff()
        crosshair2.actor.PickableOff()
        crosshair3.actor.PickableOff()
        
        self.crosshair1 = crosshair1
        self.crosshair2 = crosshair2
        self.crosshair3 = crosshair3

        self._crosshairs = {}
            
    def create_renderables(self, view):
        center = view.coordsys.world_center
        default_center = view.coordsys.default_world_center
        
        if view.name not in self._crosshairs:
            self._crosshairs[view.name] = self._create_crosshairs()
            
        crosshair1, crosshair2, crosshair3 = self._crosshairs[view.name]
        
        if isinstance(view, View2D):
            center[view.xyz[2]] = default_center[view.xyz[2]]
            
        crosshair1.pos(0, center[1], center[2])
        crosshair2.pos(center[0], 0, center[2])
        crosshair3.pos(center[0], center[1], 0)
        
        return [crosshair1, crosshair2, crosshair3]

    def _create_crosshairs(self):
        
        crosshair1 = self.crosshair1.copy()
        crosshair2 = self.crosshair2.copy()
        crosshair3 = self.crosshair3.copy()
        
        crosshair1.obj_name = f'crosshair1'
        crosshair2.obj_name = f'crosshair2'
        crosshair3.obj_name = f'crosshair3'
        
        return [crosshair1, crosshair2, crosshair3]
    