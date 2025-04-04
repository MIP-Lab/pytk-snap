from .base import Entity
import vedo
from ..colors import color_map
import numpy as np
from ..view import View2D, View3D

class Mesh3D(Entity):

    
    def __init__(self, name, vertices, triangles, shape=None, affine=None, color='red', layer=3, opacity=1, contour_eidth=3) -> None:
        super().__init__(name, layer, opacity)

        if affine is not None:
            vertices, affine = self.to_std_orientation(vertices, shape, affine)

        self.color = color
        self.affine_std = affine
        mesh = vedo.Mesh([vertices, triangles], c=self.color, alpha=self.opacity).smooth()
        mesh.name = f'{name}_mesh'
        self.mesh = mesh
        self.contour_eidth = contour_eidth    

    def create_renderables(self, view):
        
        if isinstance(view, View3D):
            return [self.mesh]
        elif isinstance(view, View2D):
            contour = self.mesh.intersect_with_plane(view.coordsys.world_center, view.camera_focal_axis)\
                .linewidth(self.contour_eidth).c(self.color)
            contour.opacity(self.opacity)
            shift = view.coordsys.default_world_center - view.coordsys.world_center
            shift[view.xyz[0]] = 0
            shift[view.xyz[1]] = 0
            shift += 0.5
            contour.shift(*shift)
            contour.pickable(True)
            contour.name = self.name
            return [contour]
        
        return []
    
    @staticmethod
    def to_std_orientation(vertices, shape, affine):
        axis_order = [0, 1, 2]
        for i in range(3):
            for j in range(3):
                affine_col = affine[:, j]
                if np.abs(affine_col).argmax() == i:
                    axis_order[i] = j
                    break
        vertices_std = vertices[:, axis_order]
        affine_std = affine[:, axis_order]
        shape_std = np.array(shape)[axis_order]
        spacing_std = np.abs(np.diag(affine_std)[: 3])
        size_std = (shape_std - 1) * spacing_std
        for i, x in enumerate([-1, -1, 1]):
            if affine_std[i, i] * x < 0:
                vertices_std[:, i] = size_std[i] - vertices_std[:, i]
                affine_std[i, i] = -affine_std[i, i]
        return vertices_std, affine_std