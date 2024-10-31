class InteractionMode:

    def __init__(self, name='') -> None:
        # self.actions = {
        #     'on_mouse_wheel_forward': [],
        #     'on_mouse_wheel_backward': [],
        #     'on_mouse_move': [],
        #     'on_left_drag': [],
        #     'on_right_drag': [],
        #     'on_middle_drag': [],
        #     'on_left_click': [],
        #     'on_left_release': [],
        #     'on_right_release': [],
        #     'on_right_click': [],
        #     'on_double_click': [],
        #     'on_key_press': [],
        #     'on_key_release': [],
        # }
        self.actions = {
            'on_button_press': {},
            'on_button_release': {},
            'on_mouse_move': {}
        }
        self.name = name
    
    def add_button_press_action(self, button, actions, priority=0):
        if button not in self.actions['on_button_press']:
            self.actions['on_button_press'][button] = []
        for action in actions:
            self.actions['on_button_press'][button].append((action, priority))
    
    def add_button_release_action(self, button, actions, priority=0):
        if button not in self.actions['on_button_release']:
            self.actions['on_button_release'][button] = []
        for action in actions:
            self.actions['on_button_release'][button].append((action, priority))
    
    def add_mouse_move_action(self, pressed_button, actions, priority=0):
        if pressed_button not in self.actions['on_mouse_move']:
            self.actions['on_mouse_move'][pressed_button] = []
        for action in actions:
            self.actions['on_mouse_move'][pressed_button].append((action, priority))
    
    def set_button_press_action(self, button, actions, priority=0):
        self.actions['on_button_press'][button] = []
        for action in actions:
            self.actions['on_button_press'][button].append((action, priority))
    
    def set_button_release_action(self, button, actions, priority=0):
        self.actions['on_button_release'][button] = []
        for action in actions:
            self.actions['on_button_release'][button].append((action, priority))
    
    def set_mouse_move_action(self, pressed_button, actions, priority=0):
        self.actions['on_mouse_move'][pressed_button] = []
        for action in actions:
            self.actions['on_mouse_move'][pressed_button].append((action, priority))
    
    # def add_action(self, event, action, priority=0, key=None):
    #     if event in ('on_key_press', 'on_key_release'):
    #         assert key is not None, 'key cannot be none'
    #         action = key_action(key, action)
    #     self.actions[event].append((action, priority))
    #     return action
    
    def remove_action(self, event, action):
        self.actions[event] = [item for item in self.actions[event] if item[0] is not action]

    def get_actions(self, event, key):

        actions = self.actions[event].get(key, [])
        sorted_actions = sorted(actions, key=lambda e: e[1], reverse=True)

        return [item[0] for item in sorted_actions]

    def build_ui(self, world, layout, default=False):
        pass
    
    def init_mode(self, world):
        pass

def view_entity_filter(view_classes=None, entity_classes=None, exclude_view_classes=None, exclude_entity_classes=None):
    if view_classes is not None and not isinstance(view_classes, tuple):
        view_classes = (view_classes, )
    if entity_classes is not None and not isinstance(entity_classes, tuple):
        entity_classes = (entity_classes, )
    if exclude_view_classes is not None and not isinstance(exclude_view_classes, tuple):
        exclude_view_classes = (exclude_view_classes, )
    if exclude_entity_classes is not None and not isinstance(exclude_entity_classes, tuple):
        exclude_entity_classes = (exclude_entity_classes, )
    def decorator(function):
        def wrapper(world, event, *args, **kwargs):
            if entity_classes is not None and not type(event.entity) in entity_classes:
                return
            if view_classes is not None and not isinstance(event.view, view_classes):
                return
            if exclude_entity_classes is not None and type(event.entity) in exclude_entity_classes:
                return
            if exclude_view_classes is not None and isinstance(event.view, exclude_view_classes):
                return
            result = function(world, event, *args, **kwargs)
            return result
        return wrapper
    return decorator

def has_picked_entity(function):
    def wrapper(world, event, *args, **kwargs):
        if event.entity is None:
            return
        result = function(world, event, *args, **kwargs)
        return result
    return wrapper

def has_picked_actor(function):
    def wrapper(world, event, *args, **kwargs):
        if event.actor_picked3d is None:
            return
        result = function(world, event, *args, **kwargs)
        return result
    return wrapper

def key_action(key, function):
    def wrapper(world, event, *args, **kwargs):
        if event.vedo_event.keypress != key:
            return
        result = function(world, event, *args, **kwargs)
        return result
    return wrapper