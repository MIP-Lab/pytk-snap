from .base import InteractionMode
from .basic_callback import *
from PyQt5 import Qt
from PyQt5.QtCore import Qt as QtQt
import time
import threading
from functools import partial

class VideoMode(InteractionMode):
    
    def __init__(self, video_coordsys) -> None:
        super().__init__(name='Video')

        self.coordsys = video_coordsys
        self.set_button_press_action('left', [move_slice_to_clicked])
        self.set_button_press_action('doubleleft', [remove_entity_from_world_in_controlpanel, remove_marker_from_world])
        self.set_button_press_action('right', [toggle_visibility_in_contropanel])
        # self.set_button_press_action('c', [add_point_marker_at_cur_location])
        # self.set_button_press_action('wheelforward', [decrease_slice_by_1])
        # self.set_button_press_action('wheelbackward', [increase_slice_by_1])
        self.set_mouse_move_action('', [show_basic_status_text])
        self.set_mouse_move_action('left', [change_opacity_in_controlpanel, rotate])
        self.set_mouse_move_action('right', [zoom])
        self.set_mouse_move_action('middle', [pan])
        self.set_mouse_move_action(('ctrl', 'left'), [change_contrast])
        
    def build_ui(self, world, layout, default=False):

        def slide(t):
            cur_coord = self.coordsys.grid_center
            self.coordsys.set_grid_center(grid_coord=np.array([cur_coord[0], cur_coord[1], t]))
            world.update_renderables(views=None, entities=None)
            world.render()
        
        def slide_dt(*args, dt):
            new_t = sp.value() + dt
            if 0 <= new_t < self.coordsys.grid_size[2]:
                sp.setValue(new_t)

        def play():
            def _play():
                cur_t = sp.value()
                sleep = 1 / 60
                for x in range(cur_t, self.coordsys.grid_size[2]):
                    sp.setValue(x)
                    # slide(x)
                    print(x)
                    time.sleep(0.2)
            thread = threading.Thread(target=_play)
            thread.start()
        
        def enter_mode():
            world.set_interaction(self.name)
        
        r0 = Qt.QRadioButton(self.name)
        if default:
            r0.toggle()
        
        r0.toggled.connect(enter_mode)

        button = Qt.QPushButton('Play')
        button.clicked.connect(play)

        sp = Qt.QSlider(QtQt.Horizontal)
        sp.setMinimum(0)
        sp.setMaximum(self.coordsys.grid_size[2] - 1)
        sp.setSingleStep(1)
        sp.setValue(self.coordsys.grid_center[2])
        sp.valueChanged.connect(slide)
        
        if default:
            r0.toggle()
        
        layout.addStretch()
        layout.addWidget(r0)
        layout.addWidget(sp)        
        layout.addWidget(r0)
        layout.addWidget(button)

        self.set_button_press_action('wheelforward', [partial(slide_dt, dt=-1)])
        self.set_button_press_action('wheelbackward', [partial(slide_dt, dt=1)])

