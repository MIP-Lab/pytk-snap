import numpy as np
import vedo
import vedo.colors
import vedo.vtkclasses as vtki
import vtk
from skimage.measure import marching_cubes
from .base import Entity
from ..view import View2D, View3D
from ..colors import colors_hex

class PointMarkerGroup(Entity):
    
    def __init__(self, name, size=5, layer=7, color='red', color_code=1) -> None:
        super().__init__(name)
        self.mesh3d = []
        self.voxel_coords = []
        self.psize = size
        self.color = color
        self.color_code = color_code
        self.layer = layer
        self.uid = 0
        self.icon_text.text(f'{self.name} ({len(self.mesh3d)})', justify='center')

    def add_marker(self, voxel_coord, world_coord):
        marker_id = self.uid + 1
        marker3d = vedo.Sphere(pos=world_coord, r=self.psize / 2, c='#' + colors_hex[self.color_code - 1])
        marker3d.obj_name = f'{self.name}_{marker_id}'
        
        marker3d.marker_id = marker_id
        
        self.uid += 1
        self.voxel_coords.append(voxel_coord)
        
        self.mesh3d.append(marker3d)
        self.icon_text.text(f'{self.name} ({len(self.mesh3d)})', justify='center')
            
    def create_renderables(self, view):    
        if isinstance(view, View3D):
            return self.mesh3d
        
        elif isinstance(view, View2D):
            slice_data = np.zeros(view.grid_size_xy)
            for p in self.voxel_coords:
                x, y, z = p[view.xyz[0]], p[view.xyz[1]], p[view.xyz[2]]
                if z == view.grid_center_z:
                    xs, ys = x - self.psize // 2, y - self.psize // 2
                    xe, ye = xs + self.psize, ys + self.psize
                    slice_data[xs: xe, ys: ye] = self.color_code
            view.set_paiting_data(slice_data, layer=self.layer, entity=self)
            return []
        return []
    
    def get_marker_by_pos(self, marker_pos):
        dist = [np.linalg.norm(marker_pos - x) for x in self.voxel_coords]
        marker = self.mesh3d[np.argmin(dist)]
        return marker
    
    def remove_one_marker(self, marker_id=None, marker_pos=None):
        if marker_id == None:
            marker = self.get_marker_by_pos(marker_pos)
            marker_id = marker.marker_id
            
        self.voxel_coords = [coords for coords, obj in zip(self.voxel_coords, self.mesh3d) if obj.marker_id != marker_id]
        self.mesh3d = [obj for obj in self.mesh3d if obj.marker_id != marker_id]
        
        self.icon_text.text(f'{self.name} ({len(self.mesh3d)})', justify='center')
    
    def remove_all_marker(self):
        self.voxel_coords = []
        self.mesh3d = []
        self.icon_text.text(f'{self.name} ({len(self.mesh3d)})', justify='center')