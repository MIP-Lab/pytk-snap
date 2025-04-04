from .base import InteractionMode
from .basic_callback import *
from PyQt5 import Qt
from PyQt5.QtCore import Qt as QtQt
from PyQt5.QtCore import pyqtSlot
import vedo.vtkclasses as vtki
from ..shapes import Box
import time
from ..colors import color_map
from PyQt5.QtGui import QFont

@has_picked_actor
@view_entity_filter(view_classes=View2D)
def brush_cursor(world, event):
    cursor = world.interaction.cursor[event.view.coordsys.id]
    try:
        pos = event.view.coordsys.grid2world(event.voxel_picked3d)
    except:
        pass
    pos[event.view.xyz[2]] = event.view.default_z
    if pos is not None:
        # cursor = vedo.Cube(pos=pos, side=4, c='red')
        cursor.pos(*pos)
        world.add_transient(event.view.at, cursor)
    world.render()

def edit_mask(world, event, v):
    s = world.interaction.paint_size
    cursor = world.interaction.cursor[event.view.coordsys.id]
    mask = world.interaction.brush_data[event.view.coordsys.id].data
    p1 = event.voxel_picked3d
    # p1 = event.vedo_event.picked3d
    pos = event.view.coordsys.grid2world(event.voxel_picked3d)
    pos[event.view.xyz[2]] = event.view.default_z
    cursor.pos(*pos)

    world.add_transient(event.view.at, cursor)

    if 'last_point' not in world.drag_tracker:
        p0 = p1
    else:
        p0 = world.drag_tracker['last_point']
    
    world.drag_tracker['last_point'] = p1.copy()

    norm_p = np.linalg.norm(p1 - p0)
    dir_p = (p1 - p0) / (norm_p + 1e-6)
    
    # print(norm_p, p1, p0)

    edit_line(mask, event.view.xyz[2], p0, p1, paint_size=s, v=v)
    view = event.view
    index = view.coordsys.grid_center[view.xyz[2]]
    order = [0, 1, 2]
    order.remove(view.xyz[2])
    order.insert(0, view.xyz[2])
    data = mask.transpose(order)[index]
    view.hot_painting(data, opacity=0.5)

    # world.update_renderables(world.get_view_by_type(View2D), list(world.interaction.brush_data.values()))
    world.render()

def update_painting_renderables(world, event):
    world.update_renderables(world.get_view_by_type(View2D), list(world.interaction.brush_data.values()))
    world.render()

def edit_line(mask, view_axis, p_start, p_end, paint_size, v):
    
    norm_p = np.linalg.norm(p_end - p_start)
    dir_p = (p_end - p_start) / (norm_p + 1e-6)
    
    line_points = [np.floor(p_start + dir_p * k).astype(np.int32) for k in range(int(norm_p) + 1)] + [p_end]
    # print(norm_p, p1, p0)
    for coords in line_points:
        order = [0, 1, 2]
        order.remove(view_axis)
        order.insert(0, view_axis)
        zz = p_start[view_axis]
        for i in range(paint_size):
            for j in range(paint_size):
                xx = coords[order[1]] - paint_size // 2 + i
                yy = coords[order[2]] - paint_size // 2 + j
                xyzv = [0, 0, 0, v]
                xyzv[order[0]] = zz
                xyzv[order[1]] = xx
                xyzv[order[2]] = yy
                # edit_point(mask, *xyzv, mode)
                mask[xyzv[0], xyzv[1], xyzv[2]] = v

@has_picked_actor
@view_entity_filter(view_classes=View2D)
def paint(world, event):
    edit_mask(world, event, world.interaction.paint_color)

@has_picked_actor
@view_entity_filter(view_classes=View2D)
def unpaint(world, event):
    edit_mask(world, event, 100)

class BrushMode(InteractionMode):
    
    def __init__(self) -> None:
        super().__init__(name='Brush')
        
        self.set_button_press_action('left', [paint])
        self.set_button_press_action('doubleleft', [remove_entity_from_world_in_controlpanel, remove_marker_from_world])
        self.set_button_press_action('right', [toggle_visibility_in_contropanel, unpaint])
        self.set_button_press_action('wheelforward', [decrease_slice_by_1])
        self.set_button_press_action('wheelbackward', [increase_slice_by_1])
        self.set_button_press_action('c', [add_point_marker_at_cur_location])
        
        self.set_mouse_move_action('', [show_basic_status_text, brush_cursor])
        self.set_mouse_move_action('left', [change_opacity_in_controlpanel, rotate, paint])
        self.set_mouse_move_action('right', [unpaint])
        self.set_mouse_move_action('middle', [pan])
        self.set_mouse_move_action(('ctrl', 'left'), [change_contrast])
        
        self.set_button_release_action('left', [update_painting_renderables])
        self.set_button_release_action('right', [update_painting_renderables])
        
        self.paint_size = 4
        
        self.brush_data = {}
        self.cursor = {}
        
        self.paint_color = 1
    
    def init_mode(self, world):
        self.brush_data = {}
        self.cursor = {}
        for cid, coordsys in world.coordsys.items():
            brush_data = IntegerMask('ISeg %s' %cid, np.zeros(coordsys.grid_size), coordsys.affine, layer=5, opacity=0.5)
            cursor = Box(self.paint_size, coordsys.spacing, lw=2, c='red')
            self.brush_data[cid] = brush_data
            self.cursor[cid] = cursor

            world.add_entity(brush_data, to_views=[view.name for view in world.views_by_coordsys[cid]])

    def build_ui(self, world, layout, default=False):
                
        def toggle():
            world.set_interaction(self.name)
        
        def choose_color(c):
            color = color_map[int(c)]
            for cursor in self.cursor.values():
                cursor.color(color[: 3])
            self.paint_color = int(c)
        
        def set_paint_size(s):
            self.paint_size = s
            new_cursors = {}
            for k, curosr in self.cursor.items():
                new_cursors[k] =  Box(self.paint_size, curosr.spacing, lw=2, c=color_map[self.paint_color][: 3])
            self.cursor = new_cursors
        
        r0 = Qt.QRadioButton(self.name)
        # r0.setFont(QFont('Times', 13))
        r1 = Qt.QComboBox()
        model = r1.model()
        for i in range(5):
            item = Qt.QStandardItem(str(i + 1))
            item.setForeground(Qt.QColor(*color_map[i + 1][: 3]))
            font = item.font()
            font.setPointSize(10)
            item.setFont(font)
            model.appendRow(item)
            
        sp = Qt.QSlider(QtQt.Horizontal)
        sp.setMinimum(1)
        sp.setMaximum(20)
        sp.setSingleStep(1)
        sp.setValue(4)
        sp.valueChanged.connect(set_paint_size)
        
        if default:
            r0.toggle()
        
        r0.toggled.connect(toggle)
        r1.currentTextChanged.connect(choose_color)
        
        layout.addStretch()
        layout.addWidget(r0)
        layout.addWidget(sp)
        layout.addWidget(r1)