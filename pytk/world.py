import multiprocessing.pool
import sys
from PyQt5 import Qt
from PyQt5.QtCore import pyqtSlot
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor # type: ignore
import vedo
# from .action import *
from functools import partial
import vtk
import vedo.utils
from .view import ControlPanel
from PyQt5.QtGui import QFont
import vedo.vtkclasses as vtki
import numpy as np
from .view import View2D, View3D
import time
import multiprocessing
from .entity import CrossHair
import gc
from collections import Counter

vtk.vtkLogger.SetStderrVerbosity(vtk.vtkLogger.VERBOSITY_OFF)


def on_double_click(self, event):
    # self._Iren.LeftButtonPressEvent()
    if event.button() == 1:
        self._Iren.MiddleButtonPressEvent()
    # print(1)

@pyqtSlot()
def on_click():
    openColorDialog()

def openColorDialog():
    color = Qt.QColorDialog.getColor()

    if color.isValid():
        print(color.name())
    
class WorldEvent:

    def __init__(self, view, entity, vedo_event=None) -> None:
        self.view = view
        self.entity = entity
        self.actor = None
        self.vedo_event = vedo_event
        self.actor_picked2d = None
        self.actor_picked3d = None
        self.world_picked3d = None
        self.voxel_picked3d = None
        self.picked_value = None

class World(Qt.QMainWindow):

    def __init__(self, view_shape=None, view_screen_size=400, view_bg='black', button_font_size=12) -> None:
        
        self.app = Qt.QApplication(sys.argv)

        button_font = QFont('Times', button_font_size)    
        self.app.setFont(button_font, "QPushButton")
        self.app.setFont(button_font, "QRadioButton")

        Qt.QMainWindow.__init__(self, None)
        self.frame = Qt.QFrame()
        self.layout = Qt.QVBoxLayout()
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
        self.vtkWidget.mouseDoubleClickEvent = partial(on_double_click, self.vtkWidget)
        if view_shape is None:
            view_elements = [
                dict(bottomleft=(0.0, 0.0), topright=(0.2, 1.0), bg='#d3d3d3'),
                dict(bottomleft=(0.2, 0.5), topright=(0.6, 1.0), bg=view_bg),
                dict(bottomleft=(0.6, 0.5), topright=(1.0, 1.0), bg=view_bg),
                dict(bottomleft=(0.6, 0.0), topright=(1.0, 0.5), bg=view_bg),
                dict(bottomleft=(0.2, 0.0), topright=(0.6, 0.5), bg=view_bg)
            ]
            screensize = (view_screen_size / 2 + view_screen_size * 2, view_screen_size * 2)

        control_width = 250

        if isinstance(view_shape, (list, tuple)):
            x_control = control_width / (control_width + (view_screen_size * view_shape[1]))
            dx = (1 - x_control) / view_shape[1]
            dy = 1 / view_shape[0]
            view_elements = [
                dict(bottomleft=(0.0, 0.0), topright=(x_control, 1.0), bg='#d3d3d3')
            ]
            for i in range(view_shape[0]):
                for j in range(view_shape[1]):
                    view_elements.append(
                        dict(bottomleft=(x_control + dx * j, 1 - dy * (i + 1)), topright=(x_control + dx * (j + 1), 1 - dy * i), bg=view_bg)
                    )
            screensize = (control_width + view_screen_size * view_shape[1], view_screen_size * view_shape[0])

        self.views_by_id = {}
        self.views = {}
        self.init_session_variables()

        self.view_shape = view_shape
        self.view_elements = view_elements
        self.screensize = screensize
        self.interaction = None
        self.camera_mode = 0
        self.default_zoom = 1
        
        self.interactions = {}
        
        self.basic_zoom = 1
        self.pressed = None
        self.ctrl_pressed = False
        self.alt_pressed = False
        
        self.interaction_swith_layout = Qt.QHBoxLayout()
        
        self.plotter = vedo.Plotter(shape=self.view_elements, screensize=self.screensize, sharecam=False, axes=0, qt_widget=self.vtkWidget)

        self.render_threads = None
        # self.dataloader = None
        self.control_panel = None
    
    def init_session_variables(self):
        self.entities = {}
        self.views_by_coordsys = {}
        self.renderables = {}
        self.coordsys = {}
        self.view_entity_binds = set()
        self.status = {}
        self.last_left_clicked = None
        self.transient_renderables = {}
        self.drag_tracker = {}

    #################################################### Object Management ######################################################################
    
        
    def add_entity(self, entity, to_views=None):
        if to_views is None:
            to_views = list(self.views)
        
        self.entities[entity.name] = entity
        for view_name in to_views:
            self.view_entity_binds.add((view_name, entity.name))
    
    def add_view(self, view, at):
        view.at = at
        self.views[view.name] = view
        self.views_by_id[at] = view
    
    def set_view_coordsys(self, coordsys, ats=None):
        ats = ats or list(self.views_by_id)
        for at in ats:
            view = self.views_by_id[at]
            view.set_coordsys(coordsys)
    
    def add_crosshair(self):
        max_size = np.zeros(3)
        for view in self.views.values():
            if view.coordsys is None:
                continue
            max_size = np.max([view.coordsys.world_size, max_size], axis=0)
        crosshair = CrossHair(max_size)
        self.add_entity(crosshair)

    def add_transient(self, ren_id, obj):
        self.transient_renderables[ren_id] = obj
    
    def get_view_by_type(self, view_type):
        views = [view for view in self.views.values() if isinstance(view, view_type)]
        return views
    
    def get_view_by_name(self, name):
        return self.views.get(name, None)
    
    def get_view_by_id(self, name):
        return self.views_by_id.get(name, None)
    
    def get_entity_by_name(self, name):
        return self.entities.get(name, None)
    
    def get_entity_by_type(self, entity_type):
        entities = [entity for entity in self.entities.values() if isinstance(entity, entity_type)]
        return entities
    
    def update_painting_slices(self, views=None):
        if views is None:
            views = self.get_view_by_type(View2D)
        for view in views:
            view.update_painting_slice()
    
    def set_renderable_opacity(self, entity):
        for obj, at in self.renderables.values():
            if hasattr(obj, 'entity') and obj.entity is entity:
                if isinstance(obj.view, ControlPanel):
                    obj.opacity(max(0.2, entity.opacity))
                else:
                    obj.opacity(entity.opacity)

        self.update_painting_slices()
        
    def remove_entity(self, entity):
        remaining_renderables = {}
        for key, (obj, at) in self.renderables.items():
            if hasattr(obj, 'entity') and obj.entity is entity:
                self.plotter.remove(obj, at=at)
            else:
                remaining_renderables[key] = (obj, at)
        self.renderables = remaining_renderables
        for view in self.views.values():
            if (view.name, entity.name) in self.view_entity_binds:
                if isinstance(view, View2D) and view.entity_in_paiting(entity):
                    view.clear_paiting_data(entity.layer)
                    view.update_painting_slice()
                
                self.view_entity_binds.remove((view.name, entity.name))
                
        self.entities.pop(entity.name)
    
    def remove_renderable(self, renderable):
        self.plotter.remove(renderable, at=renderable.view.at)
    
    def clear(self):
        # print(1)
        renderables_by_id = {}
        # obj1 = self.renderables.get('img_axial', None)
        for _, (obj, at) in self.renderables.items():
            # Memory overleak if do not use set entity to None. Reason unknown
            # if hasattr(obj, 'entity'):
            #     entity = obj.entity
            obj.entity = None
            obj.view = None
            if at not in renderables_by_id:
                renderables_by_id[at] = []
            renderables_by_id[at].append(obj)
        for at, renderables in renderables_by_id.items():
            self.plotter.remove(*renderables, at=at)
                
        self.init_session_variables()
        
    #################################################### Render Management ######################################################################
    
    @staticmethod
    def prepare_view_renderables(view, entities):
        view_renderables = []
        for entity in entities:
            renderables = entity.create_renderables(view)
            for obj in renderables:
                obj.entity = entity
                obj.view = view
                if hasattr(obj, 'obj_name'):
                    obj.view_name = f'{obj.obj_name}_{view.name}'
                else:
                    obj.view_name = f'{entity.name}_{view.name}'
                if isinstance(view, View2D) and entity.shift_at_render:
                    shift = np.array(view.camera_focal_axis) * entity.layer
                    obj.shift(*shift)
            view_renderables += renderables
        if isinstance(view, View2D):
            view.update_painting_slice()
        return view.at, view_renderables

    def update_renderables(self, views, entities):
                
        if views is None:
            views = [view for view in self.views.values() if not isinstance(view, ControlPanel)]
        
        if entities is None:
            entities = list(self.entities.values())
        
        replace_renderables = {}

        view_entities = [[view, [entity for entity in entities if (view.name, entity.name) in self.view_entity_binds]] for view in views]
        for at, view_renderables in self.render_threads.starmap(self.prepare_view_renderables, view_entities):
            replace_renderables[at] = view_renderables
        
        # for view in views:
        #     if view.at not in replace_renderables:
        #         replace_renderables[view.at] = []
        #     view_entities = [entity for entity in entities if (view.name, entity.name) in self.view_entity_binds]
        #     at, view_renderables = self.prepare_view_renderables(view, view_entities)
        #     replace_renderables[at] = view_renderables

        renderables_to_remove = dict([(at, []) for at in self.views_by_id])
        for name, (old_obj, at) in self.renderables.items():
            if hasattr(old_obj, 'entity') and old_obj.entity in entities:
                for obj in replace_renderables.get(at, []):
                    if obj is old_obj:
                        break
                else:
                    renderables_to_remove[at].append(old_obj)
        
        for at, objs in replace_renderables.items():
            add = []
            for obj in objs:
                add.append(obj)      
                self.renderables[obj.view_name] = (obj, at)
            self.plotter.remove(*renderables_to_remove[at], at=at)
            self.plotter.add(*add, at=at)
                    
        # self.replace_renderables(replace_renderables)
    
    def replace_renderables(self, renderables):
        for at, objs in renderables.items():
            remove = []
            add = []
            for obj in objs:
                old_obj, _ = self.renderables.get(obj.view_name, (None, -1))
                if obj is not old_obj:
                    if old_obj is not None:
                        remove.append(old_obj)
                    add.append(obj)      
                    self.renderables[obj.view_name] = (obj, at)
            self.plotter.remove(*remove, at=at)
            self.plotter.add(*add, at=at)
    
    def update_icons(self):
        view = self.get_view_by_type(ControlPanel)
        if len(view) > 0:
            view = view[0]
            icon_renderables = view.update_icons(list(self.entities.values()))
            self.replace_renderables({view.at: icon_renderables})
            
    def render(self):
        for k, v in self.transient_renderables.items():
            self.plotter.add(v, at=k)
        self.plotter.render()
        for k, v in self.transient_renderables.items():
            self.plotter.remove(v, at=k)
        self.transient_renderables = {}
            
    #################################################### Interaction ######################################################################
    
    def add_interaction_mode(self, interaction_mode, add_ui=True, default=True):
        if default:
            self.interaction = interaction_mode
        self.interactions[interaction_mode.name] = interaction_mode
        if add_ui:
            layout = Qt.QHBoxLayout()
            self.interaction_swith_layout.addLayout(layout)
            interaction_mode.build_ui(self, layout, default)
    
    def set_interaction(self, name):
        self.interaction = self.interactions[name]
        
    def handle_event(self, key, event):
        for action in self.interaction.get_actions(key):
            action(self, event)
    
    def warp_interaction_event(self, event):
        view = self.views_by_id[event.at]
        world_event = WorldEvent(view, entity=None, vedo_event=event)
        voxel_picked3d = view.compute_voxel_picked3d(event.picked3d)
        world_picked3d = view.compute_world_picked3d(event.picked3d)
        
        if event.actor is not None:
            if hasattr(event.actor, 'entity'):
                world_event.entity = event.actor.entity
            elif isinstance(view, View2D) and event.actor is view.painting_slice:
                world_event.entity = view.get_painting_entity(event.picked3d)
                world_event.picked_value = view.get_picked_value(voxel_picked3d)
        
        world_event.actor = event.actor
        world_event.actor_picked2d = event.picked2d
        world_event.actor_picked3d = event.picked3d
        world_event.voxel_picked3d = voxel_picked3d
        world_event.world_picked3d = world_picked3d

        return world_event
    
    def on_button_press(self, button, event):
        # disable auto repeat
        if event.keypress == '' and self.plotter.interactor.GetControlKey():
           self.ctrl_pressed = True
        event = self.warp_interaction_event(event)
        if button is None:
            button = event.vedo_event.keypress
        if self.ctrl_pressed:
            button = ('ctrl', button)
        if str(button).find('wheel') == -1:
            self.pressed = button
        for action in self.interaction.get_actions('on_button_press', button):
            action(self, event)
    
    def on_button_release(self, button, event):
        if event.keypress == '' and not self.plotter.interactor.GetControlKey():
           self.ctrl_pressed = False
        event = self.warp_interaction_event(event)
        if button is None:
            button = event.vedo_event.keypress
        for action in self.interaction.get_actions('on_button_release', button):
            action(self, event)
        self.pressed = None
        self.drag_tracker = {}
    
    def on_mouse_move(self, event):
        pressed_button = self.pressed
        if pressed_button is None:
            pressed_button = ''
        actions = self.interaction.get_actions('on_mouse_move', pressed_button)
        if len(actions) > 0:
            event = self.warp_interaction_event(event)
            for action in actions:
                action(self, event)        
    
    def add_button(self, name, func):
        button = Qt.QPushButton(name)
        button.setFont(QFont('Times', 11))
        button.clicked.connect(partial(func, self))
        self.layout.addWidget(button)
    
    def add_ratio_button(self):
        
        layout = Qt.QHBoxLayout()
        
        number_group=Qt.QButtonGroup(self.vtkWidget) # Number group
        r0=Qt.QRadioButton("0")
        number_group.addButton(r0)
        r1=Qt.QRadioButton("1")
        number_group.addButton(r1)
        
        layout.addWidget(r0)
        layout.addWidget(r1)
        
        
        button = Qt.QPushButton('Open color dialog', self)
        button.setToolTip('Opens color dialog')
        button.move(10,10)
        button.clicked.connect(on_click)
        
        layout.addWidget(button)
        
        self.layout.addLayout(layout)
    
    #################################################### Scene IO ######################################################################
    
    def set_dataloader(self, dataloader):
        dataloader.world = self
        loader_gui = dataloader.build_ui()
        self.layout.addLayout(loader_gui)
    
    #################################################### Start ######################################################################
    
    def start(self):
        
        # app = Qt.QApplication(sys.argv)
        
        self.resize(*self.screensize)
        
        self.plotter.remove_callback("KeyPress")
        
        self.plotter.add_callback("LeftButtonPresss", partial(self.on_button_press, 'left'))
        self.plotter.add_callback("LeftButtonRelease", partial(self.on_button_release, 'left'))
        
        self.plotter.add_callback("RightButtonPresss", partial(self.on_button_press, 'right'))
        self.plotter.add_callback("RightButtonRelease", partial(self.on_button_release, 'right'))
        
        self.plotter.add_callback("MiddleButtonPress", partial(self.on_button_press, 'middle'))
        self.plotter.add_callback("MiddleButtonPress", partial(self.on_button_press, 'doubleleft'))
        self.plotter.add_callback("MiddleButtonRelease", partial(self.on_button_release, 'middle'))
        
        self.plotter.add_callback("MiddleButtonPress", partial(self.on_button_press, 'middle'))
        self.plotter.add_callback("MiddleButtonRelease", partial(self.on_button_release, 'middle'))
        
        self.plotter.add_callback("MouseWheelForwardEvent", partial(self.on_button_press, 'wheelforward'))
        self.plotter.add_callback("MouseWheelBackwardEvent", partial(self.on_button_press, 'wheelbackward'))
        
        self.plotter.add_callback("KeyPress", partial(self.on_button_press, None))
        self.plotter.add_callback("KeyRelease", partial(self.on_button_release, None))
        
        self.plotter.add_callback("mouse move", self.on_mouse_move)
        
        self.render_threads = multiprocessing.pool.ThreadPool(len(self.views))

        # self.plotter.show()
        self.layout.addLayout(self.interaction_swith_layout)
        self.layout.addWidget(self.vtkWidget)
        self.frame.setLayout(self.layout)
        self.setCentralWidget(self.frame)
        self.show()
        
        # self.app.aboutToQuit.connect(self.on_close) # <-- connect the onClose event
        # self.app.exec_()
    
    def init_views(self):
        for view in self.views.values():
            if isinstance(view, View2D):
                self.replace_renderables({view.at: [view.painting_slice]})
            if not isinstance(view, ControlPanel):
                if view.coordsys.id not in self.views_by_coordsys:
                    self.views_by_coordsys[view.coordsys.id] = []
                self.views_by_coordsys[view.coordsys.id].append(view)
                if view.coordsys.id not in self.coordsys:
                    self.coordsys[view.coordsys.id] = view.coordsys
    
    def init_interactions(self):
        pass
        
    def on_start(self, zoom):
        
        self.init_views()
        
        self.add_crosshair()
        
        for renderer_id, view in self.views_by_id.items():
            camera = self.plotter.renderers[renderer_id].GetActiveCamera()
            view.set_camera(camera)
            mode = vtki.new('vtkInteractorStyleUser')
            self.plotter.at(renderer_id).show(mode=mode, zoom=1 if isinstance(view, ControlPanel) else zoom, resetcam=False)

            print(view.name, camera.GetPosition(), camera.GetFocalPoint(), camera.GetFocalDistance(), camera.GetViewUp(), 
          camera.GetDistance(), camera.GetViewAngle(), camera.GetOrientation(), camera.GetClippingRange())
        
        if self.control_panel is None:
            self.control_panel = ControlPanel()
            self.add_view(self.control_panel, at=0)
            camera = self.plotter.renderers[0].GetActiveCamera()
            self.control_panel.set_camera(camera)
            self.replace_renderables({self.control_panel.at: [self.control_panel.text]})
            self.control_panel.adjust_zoom(self.view_shape)
        
        for entity in self.entities.values():
            entity.finish_loading()
            
        self.update_renderables(views=None, entities=None)
        
        for interaction in self.interactions.values():
            interaction.init_mode(self)

        self.update_icons()
        
        self.render()
        
    
    def on_close(self, *argv):
        print('close')