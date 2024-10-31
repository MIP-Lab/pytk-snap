import numpy as np
import vedo
import vedo.vtkclasses as vtki
from .base import View

class View3D(View):

    name = '3D'
    # camera_up = (0, 1, 1)
    # camera_focal_axis = (0, 0, -1)
    camera_up = (0, 0, 1)
    camera_focal_axis = (0, -1, 0)
    camera_focal_distance = 300
    camera_parallel_projection = False
    camera_interaction_style = vtki.new("vtkInteractorStyleTrackballCamera")
    
    def compute_voxel_picked3d(self, actor_picked3d):
        if actor_picked3d is None:
            return None
        view_picked3d = actor_picked3d.copy()
        voxel_picked3d = self.coordsys.wolrd2grid(view_picked3d)
        return voxel_picked3d