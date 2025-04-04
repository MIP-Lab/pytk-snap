import numpy as np
import vedo
import vedo.vtkclasses as vtki
from .base import View

class ControlPanel(View):

    name = 'control'
    camera_parallel_projection = True
    reset_camera_according_to_object = False
    # camera_interaction_style = vtki.new("vtkInteractorStyleTrackballCamera")
    camera_interaction_style = vtki.new("vtkInteractorStyleImage")
    
    def __init__(self) -> None:
        super().__init__(coordsys=None)
        text = vedo.Text3D('-', pos=(-0.25, -0.95, -0.5), justify='bottom-left', s=0.025, c='black', font='Ubuntu')
        text.view_name = 'status'
        self.text = text
        self.start_y = 0.9
        
    def set_camera(self, camera):
        camera.SetFocalPoint(0, 0, 0)
        camera.SetPosition(0, 0, 2.2 / np.deg2rad(camera.GetViewAngle()))
        camera.SetViewUp(0, 1, 0)
        camera.SetParallelProjection(self.camera_parallel_projection)
        self.camera = camera
    
    def adjust_zoom(self, view_shape):
        text_pos = self.text.pos()
        text_pos[1] *= view_shape[0] / 2
        self.start_y *= view_shape[0] / 2
        self.text.pos(*text_pos)
        self.camera.Zoom(2 / view_shape[0])

    def display_status(self, cur_status):
        status = []
        for k, v in cur_status.items():
            status.append(f'{k}: {v}')
        
        self.text.text('\n'.join(status))
    
    def update_icons(self, entities):
        cur_x = 0
        cur_y = self.start_y
        z = -0.5
        icon_renderables = []
        for entity in entities:
            box, text = entity.icon_box, entity.icon_text
            box.pos(cur_x, cur_y, z)
            box.entity = entity
            text.entity = entity
            box.view = self
            text.view = self
            text.pos(cur_x, cur_y, z + 0.1)
            cur_y -= 0.07
            icon_renderables += [box, text]
        return icon_renderables