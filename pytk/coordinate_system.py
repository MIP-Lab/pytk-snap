import numpy as np
import vedo

class CoordinateSystem:
    pass

class DiscreteCoordinateSystem(CoordinateSystem):

    def __init__(self, grid_size, spacing, cid=0) -> None:
        self.grid_size = np.array(grid_size, dtype=np.int32)
        self.spacing = np.array(spacing)
        self.cur_grid_center = self.grid_size // 2

        self.axes = [
            np.array([1, 0, 0]),
            np.array([0, 1, 0]),
            np.array([0, 0, 1]),
        ]
        
        volumex = vedo.Volume(np.zeros([1, grid_size[1], grid_size[2]], dtype=np.uint8), spacing=spacing)
        volumey = vedo.Volume(np.zeros([grid_size[0], 1, grid_size[2]], dtype=np.uint8), spacing=spacing)
        volumez = vedo.Volume(np.zeros([grid_size[0], grid_size[1], 1], dtype=np.uint8), spacing=spacing)
        
        # virtual_volume = vedo.Volume(np.zeros(grid_size, dtype=np.uint8), spacing=spacing)
        # xslice = virtual_volume.xslice(0)
        # yslice = virtual_volume.yslice(0)
        # zslice = virtual_volume.zslice(0)
        
        xslice = volumex.xslice(0)
        yslice = volumey.yslice(0)
        zslice = volumez.zslice(0)
        self.virtual_slices = [xslice, yslice, zslice]
        
        self.id = cid

    def wolrd2grid(self, world_coord):
        return ((world_coord - 0.1) / self.spacing).round().astype(np.int32)
    
    def grid2world(self, grid_coord):
        return grid_coord * self.spacing
    
    ################################################################## voxel coord ##########################################################
    @property
    def default_grid_center(self):
        return self.grid_size // 2
    
    @property
    def grid_center(self):
        return self.cur_grid_center.copy()
    
    @property
    def affine(self):
        affine = np.array([
            [-self.spacing[0], 0, 0, 0],
            [0, -self.spacing[1], 0, 0],
            [0, 0, self.spacing[2], 0],
            [0, 0, 0, 1]]
        )
        return affine

    def set_grid_center(self, grid_coord=None, world_coord=None):
        if grid_coord is not None:
            self.cur_grid_center = grid_coord.round().astype(np.int32)
        else:
            self.cur_grid_center = self.wolrd2grid(world_coord)
    
     ################################################################## world coord ##########################################################

    @property
    def default_world_center(self):
        return self.world_size / 2

    @property
    def world_center(self):
        return self.grid_center * self.spacing
    
    @property
    def world_size(self):
        return self.grid_size * self.spacing