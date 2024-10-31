from .base import InteractionMode
from .basic_callback import *
from PyQt5 import Qt
from PyQt5.QtCore import pyqtSlot
from ..entity import Entity


class BBox(Entity):
    
    def __init__(self, name) -> None:
        super().__init__(name, layer=6, opacity=1)
        self.start_point = np.zeros(3, dtype=np.int32)
        self.min = np.zeros(3, dtype=np.int32)
        self.max = np.zeros(3, dtype=np.int32)
        self.moving = False
    
    def create_renderables(self, view):    
        if isinstance(view, View3D):
            return []
        
        elif isinstance(view, View2D):
            slice_data = np.zeros(view.grid_size_xy)
            if self.min[view.xyz[2]] <= view.grid_center_z <= self.max[view.xyz[2]]:
                hw = 1
                w = 3
                slice_data[self.min[view.xyz[0]] - hw: self.min[view.xyz[0]] + hw, self.min[view.xyz[1]]: self.max[view.xyz[1]]] = 1
                slice_data[self.max[view.xyz[0]] - hw: self.max[view.xyz[0]] + hw, self.min[view.xyz[1]]: self.max[view.xyz[1]]] = 1
                slice_data[self.min[view.xyz[0]]: self.max[view.xyz[0]], self.min[view.xyz[1]] - hw: self.min[view.xyz[1]] + hw] = 1
                slice_data[self.min[view.xyz[0]]: self.max[view.xyz[0]], self.max[view.xyz[1]] - hw: self.max[view.xyz[1]] + hw] = 1

                slice_data[self.min[view.xyz[0]] - w: self.min[view.xyz[0]] + w, self.min[view.xyz[1]] - w: self.min[view.xyz[1]] + w] = 2
                slice_data[self.min[view.xyz[0]] - w: self.min[view.xyz[0]] + w, self.max[view.xyz[1]] - w: self.max[view.xyz[1]] + w] = 2
                slice_data[self.max[view.xyz[0]] - w: self.max[view.xyz[0]] + w, self.min[view.xyz[1]] - w: self.min[view.xyz[1]] + w] = 2
                slice_data[self.max[view.xyz[0]] - w: self.max[view.xyz[0]] + w, self.max[view.xyz[1]] - w: self.max[view.xyz[1]] + w] = 2
                
            view.set_paiting_data(slice_data, layer=self.layer, entity=self)
                
            return []
        return []

@has_picked_actor
@view_entity_filter(view_classes=View2D)
def bbox_start(world, event):
    bbox = world.interaction.bbox_data[event.view.coordsys.id]
    point = event.voxel_picked3d
    start_point = np.zeros(3)
    view = event.view
    if bbox is event.entity:
        if event.picked_value == 2:
            start_point2d = []
            for i in range(2):
                j = view.xyz[i]
                if abs(point[j] - bbox.min[j]) <= abs(point[j] - bbox.max[j]):
                    start_point2d.append(bbox.max[j])
                else:
                    start_point2d.append(bbox.min[j])
            start_point[view.xyz[0]] = start_point2d[0]
            start_point[view.xyz[1]] = start_point2d[1]
            start_point[view.xyz[2]] = bbox.min[view.xyz[2]]
            bbox.start_point = start_point
    elif bbox.min[view.xyz[0]] <= point[view.xyz[0]] <= bbox.max[view.xyz[0]] and \
        bbox.min[view.xyz[1]] <= point[view.xyz[1]] <= bbox.max[view.xyz[1]]:
            bbox.moving = True
    else:
        for i in range(3):
            bbox.start_point = point.copy()
            bbox.min[i] = point[i]
            bbox.max[i] = point[i]
    
def bbox_end(world, event):
    bbox = world.interaction.bbox_data[event.view.coordsys.id]
    bbox.start_point = None
    bbox.moving = False

@has_picked_actor
@view_entity_filter(view_classes=View2D)
def bbox_drag(world, event):
    bbox = world.interaction.bbox_data[event.view.coordsys.id]
    view = event.view
    point = event.voxel_picked3d
    if bbox.start_point is None:
        if bbox.moving:
            delta3d = view.delta2d_to_delta3d(event.vedo_event.delta2d)
            delta3d /= min(10, np.sqrt(world.basic_zoom))
            bbox.min += delta3d.round().astype(np.int32)
            bbox.max += delta3d.round().astype(np.int32)
        else:
            return 
    else:
        # if event.view.name == 'axial':
        bbox.min[view.xyz[0]] = min(bbox.start_point[view.xyz[0]], point[view.xyz[0]])
        bbox.min[view.xyz[1]] = min(bbox.start_point[view.xyz[1]], point[view.xyz[1]])
        bbox.max[view.xyz[0]] = max(bbox.start_point[view.xyz[0]], point[view.xyz[0]])
        bbox.max[view.xyz[1]] = max(bbox.start_point[view.xyz[1]], point[view.xyz[1]])
    
    world.update_renderables(views=None, entities=[bbox])
    world.render()

    
class BBoxMode(InteractionMode):
    
    def __init__(self) -> None:
        super().__init__(name='BBox')
        
        self.set_button_press_action('left', [bbox_start])
        self.set_button_press_action('doubleleft', [remove_entity_from_world_in_controlpanel, remove_marker_from_world])
        self.set_button_press_action('right', [toggle_visibility_in_contropanel])
        self.set_button_press_action('wheelforward', [decrease_slice_by_1])
        self.set_button_press_action('wheelbackward', [increase_slice_by_1])
        self.set_button_press_action('c', [add_point_marker_at_cur_location])
        
        self.set_mouse_move_action('', [show_basic_status_text])
        self.set_mouse_move_action('left', [change_opacity_in_controlpanel, rotate, bbox_drag])
        self.set_mouse_move_action('right', [zoom])
        self.set_mouse_move_action('middle', [pan])
        self.set_mouse_move_action(('ctrl', 'left'), [change_contrast])
        
        self.set_button_release_action('left', [bbox_end])
        
        self.bbox_data = {}
        
    def init_mode(self, world):
        self.bbox_data = {}
        self.cursor = {}
        for cid, coordsys in world.coordsys.items():
            brush_data = BBox('BBox %s' % cid)
            self.bbox_data[cid] = brush_data
            world.add_entity(brush_data, to_views=[view.name for view in world.views_by_coordsys[cid]])

    def build_ui(self, world, layout, default=False):        
        def toggle():
            world.set_interaction(self.name)
        
        r0=Qt.QRadioButton(self.name)
        
        if default:
            r0.toggle()
        
        r0.toggled.connect(toggle)
        
        layout.addWidget(r0)