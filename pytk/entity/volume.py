from .base import Entity, Image2D
import numpy as np
from skimage.measure import marching_cubes
import vedo
from ..colors import color_map
from ..view import View2D, View3D, AxialView
from ..coordinate_system import DiscreteCoordinateSystem
import nibabel as nib
import threading
import matplotlib.pyplot as plt

def to_std_orientation(data, affine):
    axis_order = [0, 1, 2]
    for i in range(3):
        for j in range(3):
            affine_col = affine[:, j]
            if np.abs(affine_col).argmax() == i:
                axis_order[i] = j
                break
    data_std = data.transpose(axis_order)
    affine_std = affine[:, axis_order]

    for i, x in enumerate([-1, -1, 1]):
        if affine_std[i, i] * x < 0:
            data_std = np.flip(data_std, axis=i)
            affine_std[i, i] = -affine_std[i, i]
    
    return data_std, affine_std

def to_std_shape_spacing(shape, affine):
        shape = np.array(shape)
        axis_order = [0, 1, 2]
        for i in range(3):
            for j in range(3):
                affine_col = affine[:, j]
                if np.abs(affine_col).argmax() == i:
                    axis_order[i] = j
                    break
        shape_std = shape[axis_order]
        affine_std = affine[:, axis_order]

        for i, x in enumerate([-1, -1, 1]):
            if affine_std[i, i] * x < 0:
                affine_std[i, i] = -affine_std[i, i]
        
        return shape_std, np.abs([affine_std[0][0], affine_std[1][1], affine_std[2][2]])

class GrayscaleImage3D(Entity):
    
    @classmethod
    def from_numpy(cls, name, data, affine, layer=-1, opacity=1):
        image = cls(name, layer, opacity)
        image.ori_shape = data.shape
        image.ori_affine = affine

        data_std, affine_std = to_std_orientation(data, affine)
        # data_std = data_std.astype(np.float32)
        # data_std_norm = (data_std - data_std.min()) * 255 / (data_std.max() - data_std.min() + 1e-6)
        # data_std_norm = data_std_norm.round().astype(np.uint8)

        image.data = data_std
        image.affine = affine_std
        spacing = np.abs(image.affine).max(0)[: 3]
        image.shape = image.data.shape
        image.spacing = spacing
        image.size = np.array(image.data.shape) * spacing
        
        image.color_level = 127.5
        image.color_window = 255
        
        image.minv = image.data.min()
        image.maxv = image.data.max()
        
        return image
    
    @classmethod
    def from_nibabel(cls, name, file, layer=-1, opacity=1):
        
        def load_from_nibabel(nibabel_img, image):
            data, affine = np.array(nibabel_img.dataobj), nibabel_img.affine
            data_std, affine_std = to_std_orientation(data, affine)
            # data_std = data_std.astype(np.float32)
            # data_std_norm = (data_std - data_std.min()) * 255 / (data_std.max() - data_std.min() + 1e-6)
            # data_std_norm = data_std_norm.round().astype(np.uint8)
            image.data = data_std
            image.affine = affine_std
            spacing = np.abs(image.affine).max(0)[: 3]
            image.shape = image.data.shape
            image.spacing = spacing
            image.size = np.array(image.data.shape) * spacing
            
            image.minv = image.data.min()
            image.maxv = image.data.max()
            
            image.color_level = 127.5
            image.color_window = 255
        
        # image = cls(name, layer, opacity)
        nibabel_img = nib.load(file)
        # image.ori_affine = nibabel_img.affine
        # image.ori_shape = nibabel_img.shape
        
        data, affine = np.array(nibabel_img.dataobj), nibabel_img.affine
        image = cls.from_numpy(name, data, affine, layer, opacity)
        
        # image.loading_thread = threading.Thread(target=load_from_nibabel, args=[nibabel_img, image])
        # image.loading_thread.start()
        
        return image
    
    def set_min_max(self, minv=None, maxv=None):
        if minv is not None:
            self.minv = minv
        if maxv is not None:
            self.maxv = maxv
    
    def get_coordsys(self):
        shape_std, spacing_std = to_std_shape_spacing(self.ori_shape, self.ori_affine)
        coordsys = DiscreteCoordinateSystem(shape_std, spacing = spacing_std)
        return coordsys
    
    def create_renderables(self, view):

        if isinstance(view, View3D):
            return []
        
        elif isinstance(view, View2D):
            world_size = view.coordsys.world_size
            world_center = view.coordsys.default_world_center
            grid_center = view.coordsys.grid_center
            scale = view.coordsys.spacing
            if view.xyz[2] == 2:
                slice_data = self.data[::-1, :, grid_center[2]]
                slice_data[slice_data > self.maxv] = self.maxv
                slice_data[slice_data < self.minv] = self.minv
                slice_data = slice_data.astype(np.float32)
                slice_data = (slice_data - self.minv) * 255 / (self.maxv - self.minv + 1e-6)
                slice_data = slice_data.round().astype(np.uint8)
                slice = Image2D(slice_data, channels=1)
                # slice.flip('y')
                slice.actor.RotateZ(90)
                slice.actor.SetPosition([world_size[0] - 1, 0, world_center[2]])
                slice.actor.SetScale(scale[1], scale[0], scale[2])
            elif view.xyz[2] == 0:
                slice_data = self.data[grid_center[0], ::-1, :]
                slice_data[slice_data > self.maxv] = self.maxv
                slice_data[slice_data < self.minv] = self.minv
                slice_data = slice_data.astype(np.float32)
                slice_data = (slice_data - self.minv) * 255 / (self.maxv - self.minv + 1e-6)
                slice_data = slice_data.round().astype(np.uint8)
                # slice_data = np.stack([slice_data, slice_data, slice_data], axis=-1)
                slice = Image2D(slice_data, channels=1)
                # slice.flip('y')
                slice.actor.RotateY(90)
                slice.actor.RotateZ(180)
                slice.actor.SetPosition([world_center[0], world_size[1] - 1, 0])
                slice.actor.SetScale(scale[2], scale[1], scale[0])
            elif view.xyz[2] == 1:
                slice_data = self.data[::-1, grid_center[1], :]
                slice_data[slice_data > self.maxv] = self.maxv
                slice_data[slice_data < self.minv] = self.minv
                slice_data = slice_data.astype(np.float32)
                slice_data = (slice_data - self.minv) * 255 / (self.maxv - self.minv + 1e-6)
                slice_data = slice_data.round().astype(np.uint8)
                # slice_data = np.stack([slice_data, slice_data, slice_data], axis=-1)
                slice = Image2D(slice_data, channels=1)
                slice.actor.RotateZ(90)
                slice.actor.RotateY(270)
                slice.actor.SetPosition([world_size[0] - 1, world_center[1], 0])
                slice.actor.SetScale(scale[2], scale[0], scale[1])
            
            slice.properties.SetColorLevel(self.color_level)
            slice.properties.SetColorWindow(self.color_window)
            slice.shift(0.5, 0.5, 0.5)
            slice.name = self.name
            
            return [slice]
        
        return []

class IntegerMask(Entity):

    def __init__(self, name, data, affine, layer=0, opacity=1) -> None:
        super().__init__(name, layer, opacity)

        data = data.round().astype(np.uint8)
        
        data_std, affine_std = to_std_orientation(data, affine)

        self.data = data_std
        self.affine = affine_std
        spacing = np.abs(self.affine).max(0)[: 3]
        self.shape = self.data.shape
        self.spacing = spacing
        self.size = np.array(self.data.shape) * spacing

        self.ori_data = data
        self.ori_affine = affine

        self.update_3d_mesh()

    @classmethod
    def from_nibabel(cls, name, file, layer=0, opacity=1):
        
        nibabel_img = nib.load(file)
        
        data, affine = np.array(nibabel_img.dataobj), nibabel_img.affine
        image = cls(name, data, affine, layer, opacity)
        
        return image

    def update_3d_mesh(self):

        meshes = []
        for i in range(1, self.data.max() + 1):
            data_i = self.data.copy()
            data_i[data_i != i] = 0
            data_i[data_i == i] = 1
            level = (self.data.max() + self.data.min()) / 2
            verts, faces, _, _ = marching_cubes(data_i, level=level, spacing=self.spacing)
            mesh = vedo.Mesh([verts, faces], c=color_map[i][: 3], alpha=self.opacity).smooth()
            mesh.name = f'{self.name}_{i}'
            meshes.append(mesh)
        self.meshes = meshes
        return meshes
    
    def create_renderables(self, view):    
        if isinstance(view, View3D):
            return self.meshes
        
        elif isinstance(view, View2D):
            index = view.coordsys.grid_center[view.xyz[2]]
            order = [0, 1, 2]
            order.remove(view.xyz[2])
            order.insert(0, view.xyz[2])
            data = self.data.transpose(order)[index]
            view.set_paiting_data(data, layer=self.layer, entity=self)
            # view.update_painting_slice()
            return []
        return []
    
class RGBImage3D(Entity):

    @classmethod
    def from_numpy(cls, name, data, affine, cmap, layer=-1, opacity=1):
        image = cls(name, layer, opacity)
        image.ori_shape = data.shape
        image.ori_affine = affine
        image.cmap = cmap

        data_std, affine_std = to_std_orientation(data, affine)

        image.data = data_std
        image.affine = affine_std
        spacing = np.abs(image.affine).max(0)[: 3]
        image.shape = image.data.shape
        image.spacing = spacing
        image.size = np.array(image.data.shape) * spacing
        
        image.color_level = 127.5
        image.color_window = 255
        
        image.minv = image.data.min()
        image.maxv = image.data.max()
        
        return image
    
    def set_min_max(self, minv=None, maxv=None):
        if minv is not None:
            self.minv = minv
        if maxv is not None:
            self.maxv = maxv

    def get_coordsys(self):
        shape_std, spacing_std = to_std_shape_spacing(self.ori_shape, self.ori_affine)
        coordsys = DiscreteCoordinateSystem(shape_std, spacing = spacing_std)
        return coordsys
    
    def create_renderables(self, view):

        if isinstance(view, View3D):
            return []
        
        elif isinstance(view, View2D):
            world_size = view.coordsys.world_size
            world_center = view.coordsys.default_world_center
            grid_center = view.coordsys.grid_center
            scale = view.coordsys.spacing
            if view.xyz[2] == 2:
                slice_data = self.data[:, :, grid_center[2]]
                slice_data[slice_data > self.maxv] = self.maxv
                slice_data[slice_data < self.minv] = self.minv
                slice_data = slice_data.astype(np.float32)
                slice_data = (slice_data - self.minv) * 255 / (self.maxv - self.minv + 1e-6)
                slice_data = slice_data.round().astype(np.uint8)
                slice_data_rgb = self.cmap(slice_data.flatten()).reshape(slice_data.shape[0], slice_data.shape[1], 4)
                slice = Image2D((255 * slice_data_rgb[:, :, : 3]).round().astype(np.uint8), channels=3)
                slice.actor.RotateZ(90)
                slice.actor.SetPosition([world_size[0] - 1, 0, world_center[2]])
                slice.actor.SetScale(scale[1], scale[0], scale[2])
            elif view.xyz[2] == 0:
                slice_data = self.data[grid_center[0], :, :]
                slice_data[slice_data > self.maxv] = self.maxv
                slice_data[slice_data < self.minv] = self.minv
                slice_data = slice_data.astype(np.float32)
                slice_data = (slice_data - self.minv) * 255 / (self.maxv - self.minv + 1e-6)
                slice_data = slice_data.round().astype(np.uint8)
                slice_data_rgb = self.cmap(slice_data.flatten()).reshape(slice_data.shape[0], slice_data.shape[1], 4)
                slice = Image2D((255 * slice_data_rgb[:, :, : 3]).round().astype(np.uint8), channels=3)
                slice.actor.RotateY(90)
                slice.actor.RotateZ(180)
                slice.actor.SetPosition([world_center[0], world_size[1] - 1, 0])
                slice.actor.SetScale(scale[2], scale[1], scale[0])
            elif view.xyz[2] == 1:
                slice_data = self.data[:, grid_center[1], :]
                slice_data[slice_data > self.maxv] = self.maxv
                slice_data[slice_data < self.minv] = self.minv
                slice_data = slice_data.astype(np.float32)
                slice_data = (slice_data - self.minv) * 255 / (self.maxv - self.minv + 1e-6)
                slice_data = slice_data.round().astype(np.uint8)
                slice_data_rgb = self.cmap(slice_data.flatten()).reshape(slice_data.shape[0], slice_data.shape[1], 4)
                slice = Image2D((255 * slice_data_rgb[:, :, : 3]).round().astype(np.uint8), channels=3)
                slice.actor.RotateZ(90)
                slice.actor.RotateY(270)
                slice.actor.SetPosition([world_size[0] - 1, world_center[1], 0])
                slice.actor.SetScale(scale[2], scale[0], scale[1])
            
            slice.properties.SetColorLevel(self.color_level)
            slice.properties.SetColorWindow(self.color_window)
            slice.shift(0.5, 0.5, 0.5)
            slice.name = self.name
            
            return [slice]
        
        return []
    
class Video(Entity):

    def __init__(self, name, data, layer=1, opacity=1):
        super().__init__(name, layer, opacity)
        self.frames = []
        self.shape = [data.shape[2], data.shape[1], data.shape[0]]
        self.color_level = 127.5
        self.color_window = 255
        for frame_data in data:
            # frame_data = np.transpose(frame_data, [1, 0, 2])
            frame_data = np.flip(frame_data, axis=0)
            frame = Image2D(frame_data, channels=3)
            # frame.actor.RotateZ(180)
            frame.actor.SetPosition([0, 0, self.shape[2] // 2])
            frame.properties.SetColorLevel(self.color_level)
            frame.properties.SetColorWindow(self.color_window)
            frame.name = self.name
            frame.shift(0.5, 0.5, 0.5)
            self.frames.append(frame)
        self.shift_at_render = False

    def get_coordsys(self):
        coordsys = DiscreteCoordinateSystem(self.shape, spacing=[1, 1, 1])
        cur_center = coordsys.grid_center
        cur_center[2] = 0
        coordsys.set_grid_center(grid_coord=cur_center)
        return coordsys

    def create_renderables(self, view):
        grid_center = view.coordsys.grid_center
        return [self.frames[grid_center[2]]]