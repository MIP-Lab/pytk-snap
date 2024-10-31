from .base import InteractionMode
from .basic_callback import *
from PyQt5 import Qt
from PyQt5.QtGui import QFont

class NavigationMode(InteractionMode):
    
    def __init__(self) -> None:
        super().__init__(name='Navigation')

        self.set_button_press_action('left', [move_slice_to_clicked])
        self.set_button_press_action('doubleleft', [remove_entity_from_world_in_controlpanel, remove_marker_from_world])
        self.set_button_press_action('right', [toggle_visibility_in_contropanel])
        self.set_button_press_action('wheelforward', [decrease_slice_by_1])
        self.set_button_press_action('wheelbackward', [increase_slice_by_1])
        # self.set_button_press_action('c', [add_point_marker_at_cur_location])
        self.set_mouse_move_action('', [show_basic_status_text])
        self.set_mouse_move_action('left', [change_opacity_in_controlpanel, rotate])
        self.set_mouse_move_action('right', [zoom])
        self.set_mouse_move_action('middle', [pan])
        self.set_mouse_move_action(('ctrl', 'left'), [change_contrast])
        
    def build_ui(self, world, layout, default=False):
        
        def enter_mode():
            world.set_interaction(self.name)
        
        r0 = Qt.QRadioButton(self.name)
        # r0.setFont(QFont('Times', 13))
        if default:
            r0.toggle()
        
        r0.toggled.connect(enter_mode)

        layout.addWidget(r0)
