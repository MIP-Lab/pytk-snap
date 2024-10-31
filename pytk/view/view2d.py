import numpy as np
import vedo
import vedo.vtkclasses as vtki
from .base import View

import time

class View2D(View):

    xyz = (0, 1, 2)
        
    def set_coordsys(self, coordsys):
        self.coordsys = coordsys
        self.painting_slice = coordsys.virtual_slices[self.xyz[2]].copy()
        self.painting_slice.view_name = f'{self.name}_painting'
        self.painting_slice.pickable(True)
        self.painting_data = np.zeros((coordsys.grid_size[self.xyz[0]], coordsys.grid_size[self.xyz[1]], 10), dtype=np.int32)
        self.layer_opacity = np.ones(10)
        self.layer_entity_map = {}

        shift = np.array(self.camera_focal_axis) * 5
        shift[self.xyz[2]] += self.coordsys.default_world_center[self.xyz[2]]
        self.painting_slice.pos(*shift)
        self.default_z = coordsys.default_world_center[self.xyz[2]]
        
        self.update_painting_slice()

    @property
    def grid_size_xy(self):
        xyz = self.coordsys.grid_size
        return xyz[self.xyz[0]], xyz[self.xyz[1]]
    
    @property
    def grid_center_xy(self):
        xyz = self.coordsys.grid_center
        return xyz[self.xyz[0]], xyz[self.xyz[1]]
    
    @property
    def grid_size_z(self):
        return self.coordsys.grid_size[self.xyz[2]]
    
    @property
    def grid_center_z(self):
        return self.coordsys.grid_center[self.xyz[2]]
        
    @property
    def plane_position(self):
        return self.coordsys.world_center[self.xyz[2]]

    def entity_in_paiting(self, entity):
        return entity.layer in self.layer_entity_map and \
            self.layer_entity_map[entity.layer] is entity
    
    def set_paiting_data(self, data, layer, entity):
        
        assert (layer not in self.layer_entity_map) or self.layer_entity_map[layer].name == entity.name, \
        f'Cannot set painting data for: {entity.name}. Layer {layer} has been occupied by: {self.layer_entity_map[layer].name}.'
        
        self.layer_entity_map[layer] = entity
        
        self.painting_data[:, :, layer] = data + ((data != 0) * layer * 100)
    
    def hot_painting(self, data):
        data = data[: -1, : -1].T.flatten()
        colors = self.colormap[data]
        update_index = data != 0
        self.painting_slice.cellcolors[update_index] = colors[update_index]

    def clear_paiting_data(self, layer):
        self.layer_entity_map.pop(layer)
        self.painting_data[:, :, layer] = 0

    def update_painting_slice(self):
        for layer, entity in self.layer_entity_map.items():
            self.layer_opacity[layer] = entity.opacity
        # print(1)
        layer_max_index = np.argmax(self.painting_data, axis=-1, keepdims=True)
        data = np.take_along_axis(self.painting_data, layer_max_index, axis=-1)
        opacity = self.layer_opacity[layer_max_index]

        data = data[: -1, : -1, 0].T.flatten()
        opacity = opacity[: -1, : -1].T.flatten()
        # self.painting_slice.cellcolors[:, :] = 0    
        colors = self.colormap[data]
        colors[:, -1] = (colors[:, -1] != 0) * opacity * 255
            
        self.painting_slice.cellcolors = colors

    def compute_voxel_picked3d(self, actor_picked3d):
        if actor_picked3d is None:
            return None
        view_picked3d = actor_picked3d.copy()
        voxel_picked3d = self.coordsys.wolrd2grid(view_picked3d)
        voxel_picked3d[self.xyz[2]] = self.coordsys.grid_center[self.xyz[2]]
        return voxel_picked3d
    
    def compute_world_picked3d(self, actor_picked3d):
        if actor_picked3d is None:
            return None
        world_picked3d = actor_picked3d.copy()
        world_picked3d[self.xyz[2]] = self.coordsys.world_center[self.xyz[2]]
        return world_picked3d
    
    def get_picked_value(self, view_picked3d):
        x, y = view_picked3d[self.xyz[0]], view_picked3d[self.xyz[1]]
        picked_value = self.painting_data[x, y].max() % 100
        return picked_value
    
    def get_painting_entity(self, slice_picked3d):
        if slice_picked3d is None:
            return None
        
        voxel_picked3d = self.compute_voxel_picked3d(slice_picked3d)
        x, y = voxel_picked3d[self.xyz[0]], voxel_picked3d[self.xyz[1]]
        
        depth_paiting_vector = self.painting_data[x, y, :]
        selected_layer = depth_paiting_vector.argmax()

        if depth_paiting_vector[selected_layer] == 0:
            return None

        entity = self.layer_entity_map[selected_layer]

        return entity

    def slice_coord_increase(self):
        if self.coordsys.cur_grid_center[self.xyz[2]] < self.coordsys.grid_size[self.xyz[2]] - 1:
            self.coordsys.cur_grid_center += self.coordsys.axes[self.xyz[2]]
    
    def slice_coord_decrease(self):
        if self.coordsys.cur_grid_center[self.xyz[2]] > 0:
            self.coordsys.cur_grid_center -= self.coordsys.axes[self.xyz[2]]
    
class AxialView(View2D):

    name = 'axial'
    xyz = (0, 1, 2)
    camera_up = (0, -1, 0)
    camera_focal_axis = (0, 0, -1)
    camera_focal_distance = 1000
    camera_parallel_projection = True
    camera_interaction_style = vtki.new("vtkInteractorStyleImage")
    reset_camera_according_to_object = False
    # camera_interaction_style = vtki.new("vtkInteractorStyleTrackballCamera")

class SagittalView(View2D):

    name = 'sagittal'
    xyz = (1, 2, 0)
    camera_up = (0, 0, 1)
    camera_focal_axis = (1, 0, 0)
    camera_focal_distance = 1000
    camera_parallel_projection = True
    camera_interaction_style = vtki.new("vtkInteractorStyleImage")
    # camera_interaction_style = vtki.new("vtkInteractorStyleTrackballCamera")

class CoronalView(View2D):

    name = 'coronal'
    xyz = (0, 2, 1)
    camera_up = (0, 0, 1)
    camera_focal_axis = (0, -1, 0)
    camera_focal_distance = 1000
    camera_parallel_projection = True
    camera_interaction_style = vtki.new("vtkInteractorStyleImage")
    # camera_interaction_style = vtki.new("vtkInteractorStyleUser")
    # camera_interaction_style = vtki.new("vtkInteractorStyleTrackballCamera")

