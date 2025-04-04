import numpy as np
from ..colors import color_map

class View:

    name = ''
    camera_up = (0, 0, 0)
    camera_focal_axis = (0, 0, 0)
    camera_focal_distance = 0
    camera_parallel_projection = None
    reset_camera_according_to_object = False
    camera_interaction_style = None

    def __init__(self, name='', coordsys=None) -> None:
        if name != '':
            self.name = name
        self.at = None
        # self.world_size = None
        # self.world_center = None
        self.camera = None

        self.coordsys = coordsys
        
        self.colormap = color_map
        
    def set_coordsys(self, coordsys):
        self.coordsys = coordsys

    def set_camera(self, camera):

        position = self.coordsys.default_world_center + np.array(self.camera_focal_axis) * self.camera_focal_distance
        camera.SetFocalPoint(self.coordsys.default_world_center)
        camera.SetPosition(*position)
        camera.SetViewUp(*self.camera_up)
        camera.SetParallelProjection(self.camera_parallel_projection)

        if self.camera_parallel_projection:
            camera_dist = camera.GetDistance()
            angle = camera.GetViewAngle()
            world_dist = max(self.coordsys.world_size) + 5
            camera.SetClippingRange(camera_dist - world_dist, camera_dist + world_dist)
            parallel_scale = 2 * (world_dist * np.tan(0.5 * angle * np.pi / 180 ))
            camera.SetParallelScale(parallel_scale)
        else:
            camera_dist = camera.GetDistance()
            world_dist = max(self.coordsys.world_size) + 5
            angle = 2 * np.arctan(world_dist / 2 / camera_dist) * 180 / np.pi
            camera.SetViewAngle(angle)
            camera.SetClippingRange(camera_dist - world_dist, camera_dist + world_dist)
        
        self.camera = camera
    
    def compute_voxel_picked3d(self, actor_picked3d):
        if actor_picked3d is None:
            return actor_picked3d
        return actor_picked3d

    def compute_world_picked3d(self, actor_picked3d):
        if actor_picked3d is None:
            return actor_picked3d
        return actor_picked3d
    
    def delta2d_to_delta3d(self, delta2d, zoom_adjusted=True):
        camera_up = np.array(self.camera.GetViewUp())
        camera_pos = np.array(self.camera.GetPosition())
        camera_focal = np.array(self.camera.GetFocalPoint())
        camera_focal_dir = (camera_pos - camera_focal) / np.linalg.norm(camera_pos - camera_focal)
        right_dir = np.cross(camera_up, camera_focal_dir)
        delta3d = (camera_up * delta2d[1] + right_dir * delta2d[0]) * 1.0
        
        return delta3d