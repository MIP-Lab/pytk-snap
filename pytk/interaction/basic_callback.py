from .base import view_entity_filter, has_picked_entity, has_picked_actor
from ..entity import *
from ..view import View2D, View3D, ControlPanel, AxialView, CoronalView, SagittalView
import time
import numpy as np
from scipy.spatial.transform import Rotation as R
# import gc
# import objgraph

# a, b = None, None

@has_picked_entity
@view_entity_filter(view_classes=(View2D, View3D))
def move_slice_to_clicked(world, event):
    # global a, b
    # a, b, = b, [str(item) for item in gc.get_objects() if isinstance(item, tuple)]
    # print(len(a), len(b))
    # print(set(b) - set(a))
    # print(len(a), len(b))
    # print(len(world.renderables))
    # objgraph.show_most_common_types()
    # print(len(objgraph.get_leaking_objects()))
    if isinstance(event.entity, PointMarkerGroup) and isinstance(event.view, View3D):
        to_point = event.actor.pos()
        event.view.coordsys.set_grid_center(world_coord=to_point)
    elif isinstance(event.entity, PointMarkerGroup) and isinstance(event.view, View2D):
        to_point = event.entity.get_marker_by_pos(event.voxel_picked3d).pos()
        event.view.coordsys.set_grid_center(world_coord=to_point)
    else:
        to_point = event.voxel_picked3d
        event.view.coordsys.set_grid_center(grid_coord=to_point)
        
    t1 = time.time()
    world.update_renderables(views=None, entities=None)
    t2 = time.time()
    
    print(11, t2 - t1)
    
    world.render()

    t3 = time.time()
    print(22, t3 - t2, len(world.plotter.objects), len(world.renderables))

@has_picked_entity
@view_entity_filter(view_classes=View2D, entity_classes=GrayscaleImage3D)
def change_contrast(world, event):
    cur_level = event.actor.properties.GetColorLevel()
    cur_window = event.actor.properties.GetColorWindow()
    new_level = cur_level - event.vedo_event.delta2d[1]
    new_window = cur_window + event.vedo_event.delta2d[0]
    event.entity.color_level = new_level
    event.entity.color_window = new_window
    event.actor.properties.SetColorLevel(new_level)
    event.actor.properties.SetColorWindow(new_window)
    world.render()
    
@has_picked_entity
@view_entity_filter(view_classes=View2D)
def increase_slice_by_1(world, event):
    event.view.slice_coord_increase()
    world.update_renderables(views=None, entities=None)
    world.render()

@has_picked_entity
@view_entity_filter(view_classes=View2D)
def decrease_slice_by_1(world, event):
    event.view.slice_coord_decrease()
    world.update_renderables(views=None, entities=None)
    world.render()

def switch_interaction_style(world, event):
    style = event.view.camera_interaction_style
    world.set_camera_interaction_style(style)

@has_picked_entity
@view_entity_filter(view_classes=ControlPanel)
def toggle_visibility_in_contropanel(world, event):
    entity = event.entity
    entity.opacity = 0 if entity.opacity != 0 else entity.default_opacity
    
    world.set_renderable_opacity(entity)
    world.render()


@view_entity_filter(view_classes=ControlPanel)
def change_opacity_in_controlpanel(world, event):
    if abs(event.vedo_event.delta2d[0]) < abs(event.vedo_event.delta2d[1]):
        return
    if world.last_left_clicked:
        delta_opacity = 0.1 if event.vedo_event.delta2d[0] > 0 else -0.1
        entity = world.last_left_clicked
        new_opacity = entity.opacity + delta_opacity
        new_opacity = min(1, max(0, new_opacity))
        entity.opacity = new_opacity
        world.set_renderable_opacity(entity)
        world.render()
        world.render()

@view_entity_filter(view_classes=ControlPanel)
def remove_entity_from_world_in_controlpanel(world, event):
    world.remove_entity(event.entity)
    world.update_icons()
    world.render()

@has_picked_entity
@view_entity_filter(entity_classes=PointMarkerGroup, exclude_view_classes=ControlPanel)
def remove_marker_from_world(world, event):
    if isinstance(event.view, View3D):
        event.entity.remove_one_marker(marker_id=event.actor.marker_id)
        # world.remove_renderable(event.actor)
    elif isinstance(event.view, View2D):
        event.entity.remove_one_marker(marker_pos=event.voxel_picked3d)
    world.update_renderables(views=None, entities=[event.entity])
    world.render()

@has_picked_entity
def add_point_marker_at_cur_location(world, event, size=5, color='red', group_name='point marker'):
    point_marker_group = world.entities[group_name]
    voxel_coord = event.view.coordsys.grid_center
    world_coord = event.view.coordsys.world_center
    point_marker_group.add_marker(voxel_coord=voxel_coord, world_coord=world_coord)
    world.update_renderables(views=None, entities=[point_marker_group])
    world.render()

def show_basic_status_text(world, event):
    
    if event.entity is None:
        status = {}
    elif type(event.view) == ControlPanel:
        status = {}
    else:
        status = {
            'View': event.view.name,
            'Object': event.entity.name,
            '3D': np.array(event.actor_picked3d).round(1).tolist(),
            '2D': np.array(event.actor_picked2d).round(1).tolist(),
            'Voxel': event.voxel_picked3d.tolist(),
            'Value': ''
        }
        
    if event.picked_value is not None:
        status['Value'] = event.picked_value
    
    control_panel = world.get_view_by_name('control')
    if control_panel is not None:
        control_panel.display_status(status)
    
    world.render()

def zoom(world, event):
    # world.plotter.zoom(1 + 0.01 * event.vedo_event.delta2d[1])
    if isinstance(event.view, View3D):
        event.view.camera.Zoom(1 + 0.01 * event.vedo_event.delta2d[1])
    elif isinstance(event.view, View2D):
        for view in world.views_by_coordsys[event.view.coordsys.id]:
            if isinstance(view, View2D):
                view.camera.Zoom(1 + 0.01 * event.vedo_event.delta2d[1])
    world.basic_zoom += 0.01 * event.vedo_event.delta2d[1]
    world.render()

def pan(world, event):
    camera_pos = np.array(event.view.camera.GetPosition())
    camera_focal = np.array(event.view.camera.GetFocalPoint())
    delta_pos = event.view.delta2d_to_delta3d(event.vedo_event.delta2d)
    delta_pos /= min(10, np.sqrt(world.basic_zoom))
    new_pos = camera_pos - delta_pos
    new_focal = camera_focal - delta_pos
    event.view.camera.SetPosition(new_pos[0], new_pos[1], new_pos[2])
    event.view.camera.SetFocalPoint(new_focal[0], new_focal[1], new_focal[2])
    # print(event.view.camera.GetPosition(), event.view.camera.GetFocalPoint())
    world.render()

@view_entity_filter(view_classes=View3D)
def rotate(world, event):
    # camera_up = np.array(event.view.camera.GetViewUp())
    # camera_pos = np.array(event.view.camera.GetPosition())
    # camera_focal = np.array(event.view.camera.GetFocalPoint())
    # camera_focal_dir = (camera_pos - camera_focal) / np.linalg.norm(camera_pos - camera_focal)
    # right_dir = np.cross(camera_up, camera_focal_dir)

    # r1 = R.from_rotvec(right_dir * event.vedo_event.delta2d[1], degrees=True)
    # new_pos = r1.apply(camera_pos - camera_focal) + camera_focal
    # new_up = r1.apply(camera_up)

    # r2 = R.from_rotvec(-new_up * event.vedo_event.delta2d[0], degrees=True)
    # new_pos = r2.apply(new_pos - camera_focal) + camera_focal
    # # new_up = r1.apply(camera_up)
    
    # event.view.camera.SetPosition(new_pos[0], new_pos[1], new_pos[2])
    # event.view.camera.SetViewUp(new_up[0], new_up[1], new_up[2])
    # world.render()

    camera = event.view.camera
    dx = event.vedo_event.delta2d[0]
    dy = event.vedo_event.delta2d[1]
    rxf = -dx * 0.2
    ryf = -dy * 0.2
    camera.Azimuth(rxf)
    camera.Elevation(ryf)
    camera.OrthogonalizeViewUp()
    
    world.render()