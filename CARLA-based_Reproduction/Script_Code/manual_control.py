#!/usr/bin/env python

# Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

# Allows controlling a vehicle with a keyboard. For a simpler and more
# documented example, please take a look at tutorial.py.

"""
Welcome to CARLA manual control.

Use ARROWS or WASD keys for control.

    W            : throttle
    S            : brake
    A/D          : steer left/right
    Q            : toggle reverse
    Space        : hand-brake
    P            : toggle autopilot
    M            : toggle manual transmission
    ,/.          : gear up/down
    CTRL + W     : toggle constant velocity mode at 60 km/h

    L            : toggle next light type
    SHIFT + L    : toggle high beam
    Z/X          : toggle right/left blinker
    I            : toggle interior light

    TAB          : change sensor position
    ` or N       : next sensor
    [1-9]        : change to sensor [1-9]
    G            : toggle radar visualization
    C            : change weather (Shift+C reverse)
    Backspace    : change vehicle

    O            : open/close all doors of vehicle
    T            : toggle vehicle's telemetry

    V            : Select next map layer (Shift+V reverse)
    B            : Load current selected map layer (Shift+B to unload)

    R            : toggle recording images to disk

    CTRL + R     : toggle recording of simulation (replacing any previous)
    CTRL + P     : start replaying last recorded simulation
    CTRL + +     : increments the start time of the replay by 1 second (+SHIFT = 10 seconds)
    CTRL + -     : decrements the start time of the replay by 1 second (+SHIFT = 10 seconds)

    F1           : toggle HUD
    H/?          : toggle help
    ESC          : quit
"""

from __future__ import print_function


# ==============================================================================
# -- find carla module ---------------------------------------------------------
# ==============================================================================


import glob
import os 
import sys
import time

# os.environ["SDL_VIDEODRIVER"] = "dummy"

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass


# ==============================================================================
# -- imports -------------------------------------------------------------------
# ==============================================================================


import carla

from carla import ColorConverter as cc

import argparse
import collections
import datetime
import logging
import math
import random
import re
import weakref

try:
    import pygame
    from pygame.locals import KMOD_CTRL
    from pygame.locals import KMOD_SHIFT
    from pygame.locals import K_0
    from pygame.locals import K_9
    from pygame.locals import K_BACKQUOTE
    from pygame.locals import K_BACKSPACE
    from pygame.locals import K_COMMA
    from pygame.locals import K_DOWN
    from pygame.locals import K_ESCAPE
    from pygame.locals import K_F1
    from pygame.locals import K_LEFT
    from pygame.locals import K_PERIOD
    from pygame.locals import K_RIGHT
    from pygame.locals import K_SLASH
    from pygame.locals import K_SPACE
    from pygame.locals import K_TAB
    from pygame.locals import K_UP
    from pygame.locals import K_a
    from pygame.locals import K_b
    from pygame.locals import K_c
    from pygame.locals import K_d
    from pygame.locals import K_g
    from pygame.locals import K_h
    from pygame.locals import K_i
    from pygame.locals import K_l
    from pygame.locals import K_m
    from pygame.locals import K_n
    from pygame.locals import K_o
    from pygame.locals import K_p
    from pygame.locals import K_q
    from pygame.locals import K_r
    from pygame.locals import K_s
    from pygame.locals import K_t
    from pygame.locals import K_v
    from pygame.locals import K_w
    from pygame.locals import K_x
    from pygame.locals import K_z
    from pygame.locals import K_MINUS
    from pygame.locals import K_EQUALS
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')

import csv

key_list = ['x_env','v_env','y_env','a_env','staticActorX_env','staticActorY_env','RandomActorX_env','RandomActorY_env',\
        'x_ego','y_ego','a_ego','v_ego','friction','slope','AeroDrag','err','errsample','action','x_envsample','staticActorX_envsample',\
            'staticActorY_envsample','RandomActorX_envsample','RandomActorY_envsample','restrictSignalAreaX_env',\
                'signal_env','frictionsample','slopesample','t','restrictRailCrossAreaXmin_env','restrictRailCrossAreaXmax_env', 'restrictRailCrossAreaYmin_env', 'restrictRailCrossAreaYmax_env','railSignal_env',\
'restrictParkAreaXmin_env', 'restrictParkAreaXmax_env', 'restrictParkAreaYmin_env', 'restrictParkAreaYmax_env',\
'restrictUturnAreaXmin_env', 'restrictUturnAreaXmax_env', 'restrictUturnAreaYmin_env', 'restrictUturnAreaYmax_env']
info = dict()

automata_dict = dict()
automata_name_list = ['state0','state1','state2']
path = "./video/static-acc=2.8;dec=-2.8/period=1s;acc=2.8,dec=-2.8/option2/"

# ==============================================================================
# -- Global functions ----------------------------------------------------------
# ==============================================================================

FIX_ROAD_ID = 38
FIX_LANE_ID = -2
FIX_OFFSET = 81.21
START_INJECT = True
FIRST_EFFECTIVE_DATA_IDX = 3

DANGER_LIMIT = 3
SAFETY_DISTANCE = 30
CAR_ERROR = 4.847
STATIC_OBS_ERROR = 3.87
PEDESTRIAN_ERROR = 2.78


global_config = {}
def parse_acceleration_config(file_path):
    global global_config
    
    global_config.clear()
    try:
        with open(file_path, 'r') as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    try:
                        global_config[key] = float(value)
                    except ValueError:
                        print(f"Warning: Cannot parse value '{value}' (line content: '{line}')")
                else:
                    print(f"Warning: Skip error format line: '{line}'")
    except FileNotFoundError:
        print(f"Error: No file exists '{file_path}'")
        return {}
    except Exception as e:
        print(f"Parse error: {str(e)}")
        return {}

def get_config_value(key, default=None):
    global global_config
    return global_config.get(key, default)

def find_weather_presets():
    rgx = re.compile('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)')
    name = lambda x: ' '.join(m.group(0) for m in rgx.finditer(x))
    presets = [x for x in dir(carla.WeatherParameters) if re.match('[A-Z].+', x)]
    return [(getattr(carla.WeatherParameters, x), name(x)) for x in presets]


def get_actor_display_name(actor, truncate=250):
    name = ' '.join(actor.type_id.replace('_', '.').title().split('.')[1:])
    return (name[:truncate - 1] + u'\u2026') if len(name) > truncate else name

def get_actor_blueprints(world, filter, generation):
    bps = world.get_blueprint_library().filter(filter)

    if generation.lower() == "all":
        return bps

    # If the filter returns only one bp, we assume that this one needed
    # and therefore, we ignore the generation
    if len(bps) == 1:
        return bps

    try:
        int_generation = int(generation)
        # Check if generation is in available generations
        if int_generation in [1, 2]:
            bps = [x for x in bps if int(x.get_attribute('generation')) == int_generation]
            return bps
        else:
            print("   Warning! Actor Generation is not valid. No actor will be spawned.")
            return []
    except:
        print("   Warning! Actor Generation is not valid. No actor will be spawned.")
        return []


# ==============================================================================
# -- World ---------------------------------------------------------------------
# ==============================================================================


class World(object):
    def __init__(self, carla_world, hud, args):
        self.world = carla_world
        self.sync = args.sync
        self.actor_role_name = args.rolename
        try:
            self.map = self.world.get_map()
        except RuntimeError as error:
            print('RuntimeError: {}'.format(error))
            print('  The server could not send the OpenDRIVE (.xodr) file:')
            print('  Make sure it exists, has the same name of your town, and is correct.')
            sys.exit(1)
        self.hud = hud
        self.player = None
        self.collision_sensor = None
        self.lane_invasion_sensor = None
        self.gnss_sensor = None
        self.imu_sensor = None
        self.radar_sensor = None
        self.camera_manager = None
        self._weather_presets = find_weather_presets()
        self._weather_index = 0
        self._actor_filter = args.filter
        self._actor_generation = args.generation
        self._gamma = args.gamma
        self.restart()
        self.world.on_tick(hud.on_world_tick)
        self.recording_enabled = False
        self.recording_start = 0
        self.constant_velocity_enabled = False
        self.show_vehicle_telemetry = False
        self.doors_are_open = False
        self.current_map_layer = 0
        self.map_layer_names = [
            carla.MapLayer.NONE,
            carla.MapLayer.Buildings,
            carla.MapLayer.Decals,
            carla.MapLayer.Foliage,
            carla.MapLayer.Ground,
            carla.MapLayer.ParkedVehicles,
            carla.MapLayer.Particles,
            carla.MapLayer.Props,
            carla.MapLayer.StreetLights,
            carla.MapLayer.Walls,
            carla.MapLayer.All
        ]
        self.tick_idx = 0

    def restart(self):
        self.player_max_speed = 1.589
        self.player_max_speed_fast = 3.713
        # Keep same camera config if the camera manager exists.
        cam_index = self.camera_manager.index if self.camera_manager is not None else 0
        cam_pos_index = self.camera_manager.transform_index if self.camera_manager is not None else 0
        # Get a random blueprint.
        blueprint = random.choice(get_actor_blueprints(self.world, self._actor_filter, self._actor_generation))
        blueprint.set_attribute('role_name', self.actor_role_name)
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)
        if blueprint.has_attribute('driver_id'):
            driver_id = random.choice(blueprint.get_attribute('driver_id').recommended_values)
            blueprint.set_attribute('driver_id', driver_id)
        if blueprint.has_attribute('is_invincible'):
            blueprint.set_attribute('is_invincible', 'true')
        # set the max speed
        if blueprint.has_attribute('speed'):
            self.player_max_speed = float(blueprint.get_attribute('speed').recommended_values[1])
            self.player_max_speed_fast = float(blueprint.get_attribute('speed').recommended_values[2])

        # Spawn the player.
        if self.player is not None:
            spawn_point = self.player.get_transform()
            spawn_point.location.z += 2.0
            spawn_point.rotation.roll = 0.0
            spawn_point.rotation.pitch = 0.0
            self.destroy()
            self.player = self.world.try_spawn_actor(blueprint, spawn_point)
            self.show_vehicle_telemetry = False
            self.modify_vehicle_physics(self.player)
        while self.player is None:
            if not self.map.get_spawn_points():
                print('There are no spawn points available in your map/town.')
                print('Please add some Vehicle Spawn Point to your UE4 scene.')
                sys.exit(1)
            spawn_points = self.map.get_spawn_points()
            selected_wp = self.map.get_waypoint_xodr(FIX_ROAD_ID,FIX_LANE_ID,FIX_OFFSET)
            spawn_point = selected_wp.transform
            spawn_point.location.z += 2.0
            #print(spawn_point.location.x,' ',spawn_point.location.y)
            #spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
            self.player = self.world.try_spawn_actor(blueprint, spawn_point)
            self.show_vehicle_telemetry = False
            self.modify_vehicle_physics(self.player)
            # time.sleep(0.5)
            # self.player.set_enable_gravity(False)
        # Set up the sensors.
        self.collision_sensor = CollisionSensor(self.player, self.hud)
        self.lane_invasion_sensor = LaneInvasionSensor(self.player, self.hud)
        self.gnss_sensor = GnssSensor(self.player)
        self.imu_sensor = IMUSensor(self.player)
        self.camera_manager = CameraManager(self.player, self.hud, self._gamma)
        self.camera_manager.transform_index = cam_pos_index
        self.camera_manager.set_sensor(cam_index, notify=False)
        actor_type = get_actor_display_name(self.player)
        self.hud.notification(actor_type)

        if self.sync:
            self.world.tick()
        else:
            self.world.wait_for_tick()

    def next_weather(self, reverse=False):
        self._weather_index += -1 if reverse else 1
        self._weather_index %= len(self._weather_presets)
        preset = self._weather_presets[self._weather_index]
        self.hud.notification('Weather: %s' % preset[1])
        self.player.get_world().set_weather(preset[0])

    def next_map_layer(self, reverse=False):
        self.current_map_layer += -1 if reverse else 1
        self.current_map_layer %= len(self.map_layer_names)
        selected = self.map_layer_names[self.current_map_layer]
        self.hud.notification('LayerMap selected: %s' % selected)

    def load_map_layer(self, unload=False):
        selected = self.map_layer_names[self.current_map_layer]
        if unload:
            self.hud.notification('Unloading map layer: %s' % selected)
            self.world.unload_map_layer(selected)
        else:
            self.hud.notification('Loading map layer: %s' % selected)
            self.world.load_map_layer(selected)

    def toggle_radar(self):
        if self.radar_sensor is None:
            self.radar_sensor = RadarSensor(self.player)
        elif self.radar_sensor.sensor is not None:
            self.radar_sensor.sensor.destroy()
            self.radar_sensor = None

    def modify_vehicle_physics(self, actor):
        #If actor is not a vehicle, we cannot use the physics control
        try:
            physics_control = actor.get_physics_control()
            physics_control.use_sweep_wheel_collision = True
            actor.apply_physics_control(physics_control)
        except Exception:
            pass

    def tick(self, clock, action = 0):
        self.hud.tick(self, clock, action)
        self.tick_idx += 1

    def render(self, display):
        self.camera_manager.render(display)
        self.hud.render(display)

    def destroy_sensors(self):
        self.camera_manager.sensor.destroy()
        self.camera_manager.sensor = None
        self.camera_manager.index = None

    def destroy(self):
        if self.radar_sensor is not None:
            self.toggle_radar()
        sensors = [
            self.camera_manager.sensor,
            self.collision_sensor.sensor,
            self.lane_invasion_sensor.sensor,
            self.gnss_sensor.sensor,
            self.imu_sensor.sensor]
        for sensor in sensors:
            if sensor is not None:
                sensor.stop()
                sensor.destroy()
        if self.player is not None:
            self.player.destroy()
    
    def get_tick_time(self):
        return self.tick_idx


# ==============================================================================
# -- KeyboardControl -----------------------------------------------------------
# ==============================================================================


class KeyboardControl(object):
    """Class that handles keyboard input."""
    def __init__(self, world, start_in_autopilot):
        self._autopilot_enabled = start_in_autopilot
        if isinstance(world.player, carla.Vehicle):
            self._control = carla.VehicleControl()
            self._lights = carla.VehicleLightState.NONE
            world.player.set_autopilot(self._autopilot_enabled)
            world.player.set_light_state(self._lights)
        elif isinstance(world.player, carla.Walker):
            self._control = carla.WalkerControl()
            self._autopilot_enabled = False
            self._rotation = world.player.get_transform().rotation
        else:
            raise NotImplementedError("Actor type not supported")
        self._steer_cache = 0.0
        world.hud.notification("Press 'H' or '?' for help.", seconds=4.0)

    def parse_events(self, client, world, clock, sync_mode):
        if isinstance(self._control, carla.VehicleControl):
            current_lights = self._lights
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            elif event.type == pygame.KEYUP:
                if self._is_quit_shortcut(event.key):
                    return True
                elif event.key == K_BACKSPACE:
                    if self._autopilot_enabled:
                        world.player.set_autopilot(False)
                        world.restart()
                        world.player.set_autopilot(True)
                    else:
                        world.restart()
                elif event.key == K_F1:
                    world.hud.toggle_info()
                elif event.key == K_v and pygame.key.get_mods() & KMOD_SHIFT:
                    world.next_map_layer(reverse=True)
                elif event.key == K_v:
                    world.next_map_layer()
                elif event.key == K_b and pygame.key.get_mods() & KMOD_SHIFT:
                    world.load_map_layer(unload=True)
                elif event.key == K_b:
                    world.load_map_layer()
                elif event.key == K_h or (event.key == K_SLASH and pygame.key.get_mods() & KMOD_SHIFT):
                    world.hud.help.toggle()
                elif event.key == K_TAB:
                    world.camera_manager.toggle_camera()
                elif event.key == K_c and pygame.key.get_mods() & KMOD_SHIFT:
                    world.next_weather(reverse=True)
                elif event.key == K_c:
                    world.next_weather()
                elif event.key == K_g:
                    world.toggle_radar()
                elif event.key == K_BACKQUOTE:
                    world.camera_manager.next_sensor()
                elif event.key == K_n:
                    world.camera_manager.next_sensor()
                elif event.key == K_w and (pygame.key.get_mods() & KMOD_CTRL):
                    if world.constant_velocity_enabled:
                        world.player.disable_constant_velocity()
                        world.constant_velocity_enabled = False
                        world.hud.notification("Disabled Constant Velocity Mode")
                    else:
                        world.player.enable_constant_velocity(carla.Vector3D(17, 0, 0))
                        world.constant_velocity_enabled = True
                        world.hud.notification("Enabled Constant Velocity Mode at 60 km/h")
                elif event.key == K_o:
                    try:
                        if world.doors_are_open:
                            world.hud.notification("Closing Doors")
                            world.doors_are_open = False
                            world.player.close_door(carla.VehicleDoor.All)
                        else:
                            world.hud.notification("Opening doors")
                            world.doors_are_open = True
                            world.player.open_door(carla.VehicleDoor.All)
                    except Exception:
                        pass
                elif event.key == K_t:
                    if world.show_vehicle_telemetry:
                        world.player.show_debug_telemetry(False)
                        world.show_vehicle_telemetry = False
                        world.hud.notification("Disabled Vehicle Telemetry")
                    else:
                        try:
                            world.player.show_debug_telemetry(True)
                            world.show_vehicle_telemetry = True
                            world.hud.notification("Enabled Vehicle Telemetry")
                        except Exception:
                            pass
                elif event.key > K_0 and event.key <= K_9:
                    index_ctrl = 0
                    if pygame.key.get_mods() & KMOD_CTRL:
                        index_ctrl = 9
                    world.camera_manager.set_sensor(event.key - 1 - K_0 + index_ctrl)
                elif event.key == K_r and not (pygame.key.get_mods() & KMOD_CTRL):
                    world.camera_manager.toggle_recording()
                elif event.key == K_r and (pygame.key.get_mods() & KMOD_CTRL):
                    if (world.recording_enabled):
                        client.stop_recorder()
                        world.recording_enabled = False
                        world.hud.notification("Recorder is OFF")
                    else:
                        client.start_recorder("manual_recording.rec")
                        world.recording_enabled = True
                        world.hud.notification("Recorder is ON")
                elif event.key == K_p and (pygame.key.get_mods() & KMOD_CTRL):
                    # stop recorder
                    client.stop_recorder()
                    world.recording_enabled = False
                    # work around to fix camera at start of replaying
                    current_index = world.camera_manager.index
                    world.destroy_sensors()
                    # disable autopilot
                    self._autopilot_enabled = False
                    world.player.set_autopilot(self._autopilot_enabled)
                    world.hud.notification("Replaying file 'manual_recording.rec'")
                    # replayer
                    client.replay_file("manual_recording.rec", world.recording_start, 0, 0)
                    world.camera_manager.set_sensor(current_index)
                elif event.key == K_MINUS and (pygame.key.get_mods() & KMOD_CTRL):
                    if pygame.key.get_mods() & KMOD_SHIFT:
                        world.recording_start -= 10
                    else:
                        world.recording_start -= 1
                    world.hud.notification("Recording start time is %d" % (world.recording_start))
                elif event.key == K_EQUALS and (pygame.key.get_mods() & KMOD_CTRL):
                    if pygame.key.get_mods() & KMOD_SHIFT:
                        world.recording_start += 10
                    else:
                        world.recording_start += 1
                    world.hud.notification("Recording start time is %d" % (world.recording_start))
                if isinstance(self._control, carla.VehicleControl):
                    if event.key == K_q:
                        self._control.gear = 1 if self._control.reverse else -1
                    elif event.key == K_m:
                        self._control.manual_gear_shift = not self._control.manual_gear_shift
                        self._control.gear = world.player.get_control().gear
                        world.hud.notification('%s Transmission' %
                                               ('Manual' if self._control.manual_gear_shift else 'Automatic'))
                    elif self._control.manual_gear_shift and event.key == K_COMMA:
                        self._control.gear = max(-1, self._control.gear - 1)
                    elif self._control.manual_gear_shift and event.key == K_PERIOD:
                        self._control.gear = self._control.gear + 1
                    elif event.key == K_p and not pygame.key.get_mods() & KMOD_CTRL:
                        if not self._autopilot_enabled and not sync_mode:
                            print("WARNING: You are currently in asynchronous mode and could "
                                  "experience some issues with the traffic simulation")
                        self._autopilot_enabled = not self._autopilot_enabled
                        world.player.set_autopilot(self._autopilot_enabled)
                        world.hud.notification(
                            'Autopilot %s' % ('On' if self._autopilot_enabled else 'Off'))
                    elif event.key == K_l and pygame.key.get_mods() & KMOD_CTRL:
                        current_lights ^= carla.VehicleLightState.Special1
                    elif event.key == K_l and pygame.key.get_mods() & KMOD_SHIFT:
                        current_lights ^= carla.VehicleLightState.HighBeam
                    elif event.key == K_l:
                        # Use 'L' key to switch between lights:
                        # closed -> position -> low beam -> fog
                        if not self._lights & carla.VehicleLightState.Position:
                            world.hud.notification("Position lights")
                            current_lights |= carla.VehicleLightState.Position
                        else:
                            world.hud.notification("Low beam lights")
                            current_lights |= carla.VehicleLightState.LowBeam
                        if self._lights & carla.VehicleLightState.LowBeam:
                            world.hud.notification("Fog lights")
                            current_lights |= carla.VehicleLightState.Fog
                        if self._lights & carla.VehicleLightState.Fog:
                            world.hud.notification("Lights off")
                            current_lights ^= carla.VehicleLightState.Position
                            current_lights ^= carla.VehicleLightState.LowBeam
                            current_lights ^= carla.VehicleLightState.Fog
                    elif event.key == K_i:
                        current_lights ^= carla.VehicleLightState.Interior
                    elif event.key == K_z:
                        current_lights ^= carla.VehicleLightState.LeftBlinker
                    elif event.key == K_x:
                        current_lights ^= carla.VehicleLightState.RightBlinker

        if not self._autopilot_enabled:
            if isinstance(self._control, carla.VehicleControl):
                self._parse_vehicle_keys(pygame.key.get_pressed(), clock.get_time())
                self._control.reverse = self._control.gear < 0
                # Set automatic control-related vehicle lights
                if self._control.brake:
                    current_lights |= carla.VehicleLightState.Brake
                else: # Remove the Brake flag
                    current_lights &= ~carla.VehicleLightState.Brake
                if self._control.reverse:
                    current_lights |= carla.VehicleLightState.Reverse
                else: # Remove the Reverse flag
                    current_lights &= ~carla.VehicleLightState.Reverse
                if current_lights != self._lights: # Change the light state only if necessary
                    self._lights = current_lights
                    world.player.set_light_state(carla.VehicleLightState(self._lights))
            elif isinstance(self._control, carla.WalkerControl):
                self._parse_walker_keys(pygame.key.get_pressed(), clock.get_time(), world)
            world.player.apply_control(self._control)

    def _parse_vehicle_keys(self, keys, milliseconds):
        if keys[K_UP] or keys[K_w]:
            self._control.throttle = min(self._control.throttle + 0.01, 1.00)
        else:
            self._control.throttle = 0.0

        if keys[K_DOWN] or keys[K_s]:
            self._control.brake = min(self._control.brake + 0.2, 1)
        else:
            self._control.brake = 0

        steer_increment = 5e-4 * milliseconds
        if keys[K_LEFT] or keys[K_a]:
            if self._steer_cache > 0:
                self._steer_cache = 0
            else:
                self._steer_cache -= steer_increment
        elif keys[K_RIGHT] or keys[K_d]:
            if self._steer_cache < 0:
                self._steer_cache = 0
            else:
                self._steer_cache += steer_increment
        else:
            self._steer_cache = 0.0
        self._steer_cache = min(0.7, max(-0.7, self._steer_cache))
        self._control.steer = round(self._steer_cache, 1)
        self._control.hand_brake = keys[K_SPACE]

    def _parse_walker_keys(self, keys, milliseconds, world):
        self._control.speed = 0.0
        if keys[K_DOWN] or keys[K_s]:
            self._control.speed = 0.0
        if keys[K_LEFT] or keys[K_a]:
            self._control.speed = .01
            self._rotation.yaw -= 0.08 * milliseconds
        if keys[K_RIGHT] or keys[K_d]:
            self._control.speed = .01
            self._rotation.yaw += 0.08 * milliseconds
        if keys[K_UP] or keys[K_w]:
            self._control.speed = world.player_max_speed_fast if pygame.key.get_mods() & KMOD_SHIFT else world.player_max_speed
        self._control.jump = keys[K_SPACE]
        self._rotation.yaw = round(self._rotation.yaw, 1)
        self._control.direction = self._rotation.get_forward_vector()

    @staticmethod
    def _is_quit_shortcut(key):
        return (key == K_ESCAPE) or (key == K_q and pygame.key.get_mods() & KMOD_CTRL)


# ==============================================================================
# -- HUD -----------------------------------------------------------------------
# ==============================================================================


class HUD(object):
    def __init__(self, width, height):
        self.dim = (width, height)
        font = pygame.font.Font(pygame.font.get_default_font(), 20)
        font_name = 'courier' if os.name == 'nt' else 'mono'
        fonts = [x for x in pygame.font.get_fonts() if font_name in x]
        default_font = 'ubuntumono'
        mono = default_font if default_font in fonts else fonts[0]
        mono = pygame.font.match_font(mono)
        self._font_mono = pygame.font.Font(mono, 12 if os.name == 'nt' else 14)
        self._notifications = FadingText(font, (width, 40), (0, height - 40))
        self.help = HelpText(pygame.font.Font(mono, 16), width, height)
        self.server_fps = 0
        self.frame = 0
        self.simulation_time = 0
        self._show_info = True
        self._info_text = []
        self._server_clock = pygame.time.Clock()
        self.data_length = len(info[key_list[0]])
        self.idx = 0
        self.tick_count = 0
        self.is_collision = False

    def on_world_tick(self, timestamp):
        self._server_clock.tick()
        self.server_fps = self._server_clock.get_fps()
        self.frame = timestamp.frame
        self.simulation_time = timestamp.elapsed_seconds

    def tick(self, world, clock, action = 0):
        self._notifications.tick(world, clock)
        if not self._show_info:
            return
        t = world.player.get_transform()
        v = world.player.get_velocity()
        c = world.player.get_control()
        compass = world.imu_sensor.compass
        heading = 'N' if compass > 270.5 or compass < 89.5 else ''
        heading += 'S' if 90.5 < compass < 269.5 else ''
        heading += 'E' if 0.5 < compass < 179.5 else ''
        heading += 'W' if 180.5 < compass < 359.5 else ''
        colhist = world.collision_sensor.get_collision_history()
        collision = [colhist[x + self.frame - 200] for x in range(0, 200)]
        max_col = max(1.0, max(collision))
        collision = [x / max_col for x in collision]
        vehicles = world.world.get_actors().filter('vehicle.*')
        static_obstacle = world.world.get_actors().filter('static.prop.*')
        self._info_text = [
            'Server:  % 16.0f FPS' % self.server_fps,
            'Client:  % 16.0f FPS' % clock.get_fps(),
            '',
            'Vehicle: % 20s' % get_actor_display_name(world.player, truncate=20),
            'Map:     % 20s' % world.map.name.split('/')[-1],
            'Simulation time: % 12s' % datetime.timedelta(seconds=int(self.simulation_time)),
            '',
            'Speed:   % 15.0f km/h' % (3.6 * math.sqrt(v.x**2 + v.y**2 + v.z**2)),
            u'Compass:% 17.0f\N{DEGREE SIGN} % 2s' % (compass, heading),
            'Accelero: (%5.1f,%5.1f,%5.1f)' % (world.imu_sensor.accelerometer),
            'Location:% 20s' % ('(% 5.1f, % 5.1f)' % (t.location.x, t.location.y)),
            'Height:  % 18.0f m' % t.location.z,
            '',
            'Friction: %16s' % info['friction'][self.idx],
            'Slope: %20s' % info['slope'][self.idx],
            'AeroDrag: %15s' % info['AeroDrag'][self.idx],
            'Err: %23s' % info['err'][self.idx],
            'Action: %12s' % action]
        if isinstance(c, carla.VehicleControl):
            self._info_text += [
                ('Throttle:', c.throttle, 0.0, 1.0),
                ('Steer:', c.steer, -1.0, 1.0),
                ('Brake:', c.brake, 0.0, 1.0),
                ('Reverse:', c.reverse),
                ('Hand brake:', c.hand_brake),
                ('Manual:', c.manual_gear_shift),
                'Gear:        %s' % {-1: 'R', 0: 'N'}.get(c.gear, c.gear)]
        elif isinstance(c, carla.WalkerControl):
            self._info_text += [
                ('Speed:', c.speed, 0.0, 5.556),
                ('Jump:', c.jump)]
        self._info_text += [
            '',
            'Collision:',
            collision,
            '',
            'Number of vehicles: % 8d' % len(vehicles)]
        self._info_text += ['Nearby static obstacle:']
        distance = lambda l: math.sqrt((l.x - t.location.x)**2 + (l.y - t.location.y)**2 + (l.z - t.location.z)**2)
        static_obstacles = [(distance(x.get_location()), x) for x in static_obstacle if x.id != world.player.id]
        for d, st_obs in sorted(static_obstacles, key=lambda static_obstacles: static_obstacles[0]):
            self._info_text.append('% .2fm %s' % (d, st_obs.type_id))
        
        self._info_text += ['Nearby pedestrians:']
        pedestrians = world.world.get_actors().filter('walker.pedestrian.*')
        distance = lambda l: math.sqrt((l.x - t.location.x)**2 + (l.y - t.location.y)**2 + (l.z - t.location.z)**2)
        pedestrians = [(distance(x.get_location()), x) for x in pedestrians if x.id != world.player.id]
        for d, pedestrian in sorted(pedestrians, key=lambda pedestrians: pedestrians[0]):
            self._info_text.append('% .2fm %s' % (d, pedestrian.type_id))

        if len(vehicles) > 1:
            self._info_text += ['Nearby vehicles:']
            distance = lambda l: math.sqrt((l.x - t.location.x)**2 + (l.y - t.location.y)**2 + (l.z - t.location.z)**2)
            vehicles = [(distance(x.get_location()), x) for x in vehicles if x.id != world.player.id]
            for d, vehicle in sorted(vehicles, key=lambda vehicles: vehicles[0]):
                if d > 200.0:
                    break
                vehicle_type = get_actor_display_name(vehicle, truncate=22)
                self._info_text.append('% .2fm %s' % (d, vehicle_type))
                
        if START_INJECT == 1:
            self.tick_count += 1
            if self.tick_count % 10 == 0:
                self.idx = self.idx + 1
            if self.idx == self.data_length:
                self.idx = self.data_length - 1
        
        
        
    def toggle_info(self):
        self._show_info = not self._show_info

    def notification(self, text, seconds=2.0):
        self._notifications.set_text(text, seconds=seconds)

    def error(self, text):
        self._notifications.set_text('Error: %s' % text, (255, 0, 0))

    def render(self, display):
        if self._show_info:
            info_surface = pygame.Surface((220, self.dim[1]))
            info_surface.set_alpha(100)
            display.blit(info_surface, (0, 0))
            v_offset = 4
            bar_h_offset = 100
            bar_width = 106
            for item in self._info_text:
                if v_offset + 18 > self.dim[1]:
                    break
                if isinstance(item, list):
                    if len(item) > 1:
                        points = [(x + 8, v_offset + 8 + (1.0 - y) * 30) for x, y in enumerate(item)]
                        pygame.draw.lines(display, (255, 136, 0), False, points, 2)
                    item = None
                    v_offset += 18
                elif isinstance(item, tuple):
                    if isinstance(item[1], bool):
                        rect = pygame.Rect((bar_h_offset, v_offset + 8), (6, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect, 0 if item[1] else 1)
                    else:
                        rect_border = pygame.Rect((bar_h_offset, v_offset + 8), (bar_width, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect_border, 1)
                        f = (item[1] - item[2]) / (item[3] - item[2])
                        if item[2] < 0.0:
                            rect = pygame.Rect((bar_h_offset + f * (bar_width - 6), v_offset + 8), (6, 6))
                        else:
                            rect = pygame.Rect((bar_h_offset, v_offset + 8), (f * bar_width, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect)
                    item = item[0]
                if item:  # At this point has to be a str.
                    surface = self._font_mono.render(item, True, (255, 255, 255))
                    display.blit(surface, (8, v_offset))
                v_offset += 18
        self._notifications.render(display)
        self.help.render(display)


# ==============================================================================
# -- FadingText ----------------------------------------------------------------
# ==============================================================================


class FadingText(object):
    def __init__(self, font, dim, pos):
        self.font = font
        self.dim = dim
        self.pos = pos
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)

    def set_text(self, text, color=(255, 255, 255), seconds=2.0):
        text_texture = self.font.render(text, True, color)
        self.surface = pygame.Surface(self.dim)
        self.seconds_left = seconds
        self.surface.fill((0, 0, 0, 0))
        self.surface.blit(text_texture, (10, 11))

    def tick(self, _, clock):
        delta_seconds = 1e-3 * clock.get_time()
        self.seconds_left = max(0.0, self.seconds_left - delta_seconds)
        self.surface.set_alpha(500.0 * self.seconds_left)

    def render(self, display):
        display.blit(self.surface, self.pos)


# ==============================================================================
# -- HelpText ------------------------------------------------------------------
# ==============================================================================


class HelpText(object):
    """Helper class to handle text output using pygame"""
    def __init__(self, font, width, height):
        lines = __doc__.split('\n')
        self.font = font
        self.line_space = 18
        self.dim = (780, len(lines) * self.line_space + 12)
        self.pos = (0.5 * width - 0.5 * self.dim[0], 0.5 * height - 0.5 * self.dim[1])
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)
        self.surface.fill((0, 0, 0, 0))
        for n, line in enumerate(lines):
            text_texture = self.font.render(line, True, (255, 255, 255))
            self.surface.blit(text_texture, (22, n * self.line_space))
            self._render = False
        self.surface.set_alpha(220)

    def toggle(self):
        self._render = not self._render

    def render(self, display):
        if self._render:
            display.blit(self.surface, self.pos)


# ==============================================================================
# -- CollisionSensor -----------------------------------------------------------
# ==============================================================================


class CollisionSensor(object):
    def __init__(self, parent_actor, hud):
        self.sensor = None
        self.history = []
        self._parent = parent_actor
        self.hud = hud
        world = self._parent.get_world()
        bp = world.get_blueprint_library().find('sensor.other.collision')
        self.sensor = world.spawn_actor(bp, carla.Transform(), attach_to=self._parent)
        # We need to pass the lambda a weak reference to self to avoid circular
        # reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: CollisionSensor._on_collision(weak_self, event))

    def get_collision_history(self):
        history = collections.defaultdict(int)
        for frame, intensity in self.history:
            history[frame] += intensity
        return history

    @staticmethod
    def _on_collision(weak_self, event):
        self = weak_self()
        if not self:
            return
        actor_type = get_actor_display_name(event.other_actor)
        self.hud.notification('Collision with %r' % actor_type)
        self.hud.is_collision = True
        impulse = event.normal_impulse
        intensity = math.sqrt(impulse.x**2 + impulse.y**2 + impulse.z**2)
        self.history.append((event.frame, intensity))
        if len(self.history) > 4000:
            self.history.pop(0)


# ==============================================================================
# -- LaneInvasionSensor --------------------------------------------------------
# ==============================================================================


class LaneInvasionSensor(object):
    def __init__(self, parent_actor, hud):
        self.sensor = None

        # If the spawn object is not a vehicle, we cannot use the Lane Invasion Sensor
        if parent_actor.type_id.startswith("vehicle."):
            self._parent = parent_actor
            self.hud = hud
            world = self._parent.get_world()
            bp = world.get_blueprint_library().find('sensor.other.lane_invasion')
            self.sensor = world.spawn_actor(bp, carla.Transform(), attach_to=self._parent)
            # We need to pass the lambda a weak reference to self to avoid circular
            # reference.
            weak_self = weakref.ref(self)
            self.sensor.listen(lambda event: LaneInvasionSensor._on_invasion(weak_self, event))

    @staticmethod
    def _on_invasion(weak_self, event):
        self = weak_self()
        if not self:
            return
        lane_types = set(x.type for x in event.crossed_lane_markings)
        text = ['%r' % str(x).split()[-1] for x in lane_types]
        self.hud.notification('Crossed line %s' % ' and '.join(text))


# ==============================================================================
# -- GnssSensor ----------------------------------------------------------------
# ==============================================================================


class GnssSensor(object):
    def __init__(self, parent_actor):
        self.sensor = None
        self._parent = parent_actor
        self.lat = 0.0
        self.lon = 0.0
        world = self._parent.get_world()
        bp = world.get_blueprint_library().find('sensor.other.gnss')
        self.sensor = world.spawn_actor(bp, carla.Transform(carla.Location(x=1.0, z=2.8)), attach_to=self._parent)
        # We need to pass the lambda a weak reference to self to avoid circular
        # reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: GnssSensor._on_gnss_event(weak_self, event))

    @staticmethod
    def _on_gnss_event(weak_self, event):
        self = weak_self()
        if not self:
            return
        self.lat = event.latitude
        self.lon = event.longitude


# ==============================================================================
# -- IMUSensor -----------------------------------------------------------------
# ==============================================================================


class IMUSensor(object):
    def __init__(self, parent_actor):
        self.sensor = None
        self._parent = parent_actor
        self.accelerometer = (0.0, 0.0, 0.0)
        self.gyroscope = (0.0, 0.0, 0.0)
        self.compass = 0.0
        world = self._parent.get_world()
        bp = world.get_blueprint_library().find('sensor.other.imu')
        self.sensor = world.spawn_actor(
            bp, carla.Transform(), attach_to=self._parent)
        # We need to pass the lambda a weak reference to self to avoid circular
        # reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(
            lambda sensor_data: IMUSensor._IMU_callback(weak_self, sensor_data))

    @staticmethod
    def _IMU_callback(weak_self, sensor_data):
        self = weak_self()
        if not self:
            return
        limits = (-99.9, 99.9)
        self.accelerometer = (
            max(limits[0], min(limits[1], sensor_data.accelerometer.x)),
            max(limits[0], min(limits[1], sensor_data.accelerometer.y)),
            max(limits[0], min(limits[1], sensor_data.accelerometer.z)))
        self.gyroscope = (
            max(limits[0], min(limits[1], math.degrees(sensor_data.gyroscope.x))),
            max(limits[0], min(limits[1], math.degrees(sensor_data.gyroscope.y))),
            max(limits[0], min(limits[1], math.degrees(sensor_data.gyroscope.z))))
        self.compass = math.degrees(sensor_data.compass)


# ==============================================================================
# -- RadarSensor ---------------------------------------------------------------
# ==============================================================================


class RadarSensor(object):
    def __init__(self, parent_actor):
        self.sensor = None
        self._parent = parent_actor
        bound_x = 0.5 + self._parent.bounding_box.extent.x
        bound_y = 0.5 + self._parent.bounding_box.extent.y
        bound_z = 0.5 + self._parent.bounding_box.extent.z

        self.velocity_range = 7.5 # m/s
        world = self._parent.get_world()
        self.debug = world.debug
        bp = world.get_blueprint_library().find('sensor.other.radar')
        bp.set_attribute('horizontal_fov', str(35))
        bp.set_attribute('vertical_fov', str(20))
        self.sensor = world.spawn_actor(
            bp,
            carla.Transform(
                carla.Location(x=bound_x + 0.05, z=bound_z+0.05),
                carla.Rotation(pitch=5)),
            attach_to=self._parent)
        # We need a weak reference to self to avoid circular reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(
            lambda radar_data: RadarSensor._Radar_callback(weak_self, radar_data))

    @staticmethod
    def _Radar_callback(weak_self, radar_data):
        self = weak_self()
        if not self:
            return
        # To get a numpy [[vel, altitude, azimuth, depth],...[,,,]]:
        # points = np.frombuffer(radar_data.raw_data, dtype=np.dtype('f4'))
        # points = np.reshape(points, (len(radar_data), 4))

        current_rot = radar_data.transform.rotation
        for detect in radar_data:
            azi = math.degrees(detect.azimuth)
            alt = math.degrees(detect.altitude)
            # The 0.25 adjusts a bit the distance so the dots can
            # be properly seen
            fw_vec = carla.Vector3D(x=detect.depth - 0.25)
            carla.Transform(
                carla.Location(),
                carla.Rotation(
                    pitch=current_rot.pitch + alt,
                    yaw=current_rot.yaw + azi,
                    roll=current_rot.roll)).transform(fw_vec)

            def clamp(min_v, max_v, value):
                return max(min_v, min(value, max_v))

            norm_velocity = detect.velocity / self.velocity_range # range [-1, 1]
            r = int(clamp(0.0, 1.0, 1.0 - norm_velocity) * 255.0)
            g = int(clamp(0.0, 1.0, 1.0 - abs(norm_velocity)) * 255.0)
            b = int(abs(clamp(- 1.0, 0.0, - 1.0 - norm_velocity)) * 255.0)
            self.debug.draw_point(
                radar_data.transform.location + fw_vec,
                size=0.075,
                life_time=0.06,
                persistent_lines=False,
                color=carla.Color(r, g, b))

# ==============================================================================
# -- CameraManager -------------------------------------------------------------
# ==============================================================================


class CameraManager(object):
    def __init__(self, parent_actor, hud, gamma_correction):
        self.sensor = None
        self.surface = None
        self._parent = parent_actor
        self.hud = hud
        self.recording = False
        bound_x = 0.5 + self._parent.bounding_box.extent.x
        bound_y = 0.5 + self._parent.bounding_box.extent.y
        bound_z = 0.5 + self._parent.bounding_box.extent.z
        Attachment = carla.AttachmentType

        if not self._parent.type_id.startswith("walker.pedestrian"):
            self._camera_transforms = [
                (carla.Transform(carla.Location(x=-2.0*bound_x, y=+0.0*bound_y, z=2.0*bound_z), carla.Rotation(pitch=8.0)), Attachment.SpringArm),
                (carla.Transform(carla.Location(x=+0.8*bound_x, y=+0.0*bound_y, z=1.3*bound_z)), Attachment.Rigid),
                (carla.Transform(carla.Location(x=+1.9*bound_x, y=+1.0*bound_y, z=1.2*bound_z)), Attachment.SpringArm),
                (carla.Transform(carla.Location(x=-2.8*bound_x, y=+0.0*bound_y, z=4.6*bound_z), carla.Rotation(pitch=6.0)), Attachment.SpringArm),
                (carla.Transform(carla.Location(x=-1.0, y=-1.0*bound_y, z=0.4*bound_z)), Attachment.Rigid)]
        else:
            self._camera_transforms = [
                (carla.Transform(carla.Location(x=-2.5, z=0.0), carla.Rotation(pitch=-8.0)), Attachment.SpringArm),
                (carla.Transform(carla.Location(x=1.6, z=1.7)), Attachment.Rigid),
                (carla.Transform(carla.Location(x=2.5, y=0.5, z=0.0), carla.Rotation(pitch=-8.0)), Attachment.SpringArm),
                (carla.Transform(carla.Location(x=-4.0, z=2.0), carla.Rotation(pitch=6.0)), Attachment.SpringArm),
                (carla.Transform(carla.Location(x=0, y=-2.5, z=-0.0), carla.Rotation(yaw=90.0)), Attachment.Rigid)]

        self.transform_index = 1
        self.sensors = [
            ['sensor.camera.rgb', cc.Raw, 'Camera RGB', {}],
            ['sensor.camera.depth', cc.Raw, 'Camera Depth (Raw)', {}],
            ['sensor.camera.depth', cc.Depth, 'Camera Depth (Gray Scale)', {}],
            ['sensor.camera.depth', cc.LogarithmicDepth, 'Camera Depth (Logarithmic Gray Scale)', {}],
            ['sensor.camera.semantic_segmentation', cc.Raw, 'Camera Semantic Segmentation (Raw)', {}],
            ['sensor.camera.semantic_segmentation', cc.CityScapesPalette, 'Camera Semantic Segmentation (CityScapes Palette)', {}],
            ['sensor.camera.instance_segmentation', cc.CityScapesPalette, 'Camera Instance Segmentation (CityScapes Palette)', {}],
            ['sensor.camera.instance_segmentation', cc.Raw, 'Camera Instance Segmentation (Raw)', {}],
            ['sensor.lidar.ray_cast', None, 'Lidar (Ray-Cast)', {'range': '50'}],
            ['sensor.camera.dvs', cc.Raw, 'Dynamic Vision Sensor', {}],
            ['sensor.camera.rgb', cc.Raw, 'Camera RGB Distorted',
                {'lens_circle_multiplier': '3.0',
                'lens_circle_falloff': '3.0',
                'chromatic_aberration_intensity': '0.5',
                'chromatic_aberration_offset': '0'}],
            ['sensor.camera.optical_flow', cc.Raw, 'Optical Flow', {}],
        ]
        world = self._parent.get_world()
        bp_library = world.get_blueprint_library()
        for item in self.sensors:
            bp = bp_library.find(item[0])
            if item[0].startswith('sensor.camera'):
                bp.set_attribute('image_size_x', str(hud.dim[0]))
                bp.set_attribute('image_size_y', str(hud.dim[1]))
                if bp.has_attribute('gamma'):
                    bp.set_attribute('gamma', str(gamma_correction))
                for attr_name, attr_value in item[3].items():
                    bp.set_attribute(attr_name, attr_value)
            elif item[0].startswith('sensor.lidar'):
                self.lidar_range = 50

                for attr_name, attr_value in item[3].items():
                    bp.set_attribute(attr_name, attr_value)
                    if attr_name == 'range':
                        self.lidar_range = float(attr_value)

            item.append(bp)
        self.index = None

    def toggle_camera(self):
        self.transform_index = (self.transform_index + 1) % len(self._camera_transforms)
        self.set_sensor(self.index, notify=False, force_respawn=True)

    def set_sensor(self, index, notify=True, force_respawn=False):
        index = index % len(self.sensors)
        needs_respawn = True if self.index is None else \
            (force_respawn or (self.sensors[index][2] != self.sensors[self.index][2]))
        if needs_respawn:
            if self.sensor is not None:
                self.sensor.destroy()
                self.surface = None
            self.sensor = self._parent.get_world().spawn_actor(
                self.sensors[index][-1],
                self._camera_transforms[self.transform_index][0],
                attach_to=self._parent,
                attachment_type=self._camera_transforms[self.transform_index][1])
            # We need to pass the lambda a weak reference to self to avoid
            # circular reference.
            weak_self = weakref.ref(self)
            self.sensor.listen(lambda image: CameraManager._parse_image(weak_self, image))
        if notify:
            self.hud.notification(self.sensors[index][2])
        self.index = index

    def next_sensor(self):
        self.set_sensor(self.index + 1)

    def toggle_recording(self):
        self.recording = not self.recording
        self.hud.notification('Recording %s' % ('On' if self.recording else 'Off'))

    def render(self, display):
        if self.surface is not None:
            display.blit(self.surface, (0, 0))

    @staticmethod
    def _parse_image(weak_self, image):
        self = weak_self()
        if not self:
            return
        if self.sensors[self.index][0].startswith('sensor.lidar'):
            points = np.frombuffer(image.raw_data, dtype=np.dtype('f4'))
            points = np.reshape(points, (int(points.shape[0] / 4), 4))
            lidar_data = np.array(points[:, :2])
            lidar_data *= min(self.hud.dim) / (2.0 * self.lidar_range)
            lidar_data += (0.5 * self.hud.dim[0], 0.5 * self.hud.dim[1])
            lidar_data = np.fabs(lidar_data)  # pylint: disable=E1111
            lidar_data = lidar_data.astype(np.int32)
            lidar_data = np.reshape(lidar_data, (-1, 2))
            lidar_img_size = (self.hud.dim[0], self.hud.dim[1], 3)
            lidar_img = np.zeros((lidar_img_size), dtype=np.uint8)
            lidar_img[tuple(lidar_data.T)] = (255, 255, 255)
            self.surface = pygame.surfarray.make_surface(lidar_img)
        elif self.sensors[self.index][0].startswith('sensor.camera.dvs'):
            # Example of converting the raw_data from a carla.DVSEventArray
            # sensor into a NumPy array and using it as an image
            dvs_events = np.frombuffer(image.raw_data, dtype=np.dtype([
                ('x', np.uint16), ('y', np.uint16), ('t', np.int64), ('pol', np.bool)]))
            dvs_img = np.zeros((image.height, image.width, 3), dtype=np.uint8)
            # Blue is positive, red is negative
            dvs_img[dvs_events[:]['y'], dvs_events[:]['x'], dvs_events[:]['pol'] * 2] = 255
            self.surface = pygame.surfarray.make_surface(dvs_img.swapaxes(0, 1))
        elif self.sensors[self.index][0].startswith('sensor.camera.optical_flow'):
            image = image.get_color_coded_flow()
            array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
            array = np.reshape(array, (image.height, image.width, 4))
            array = array[:, :, :3]
            array = array[:, :, ::-1]
            self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
        else:
            image.convert(self.sensors[self.index][1])
            array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
            array = np.reshape(array, (image.height, image.width, 4))
            array = array[:, :, :3]
            array = array[:, :, ::-1]
            self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
        if self.recording:
            image.save_to_disk('_out/%08d' % image.frame)


# ==============================================================================
# -- game_loop() ---------------------------------------------------------------
# ==============================================================================


def game_loop(args):
    pygame.init()
    pygame.font.init()
    world = None
    original_settings = None

    try:
        client = carla.Client(args.host, args.port)
        client.set_timeout(20.0)

        sim_world = client.get_world()
        if args.sync:
            original_settings = sim_world.get_settings()
            settings = sim_world.get_settings()
            if not settings.synchronous_mode:
                settings.synchronous_mode = True
                settings.fixed_delta_seconds = 0.05
            sim_world.apply_settings(settings)

            traffic_manager = client.get_trafficmanager()
            traffic_manager.set_synchronous_mode(True)

        if args.autopilot and not sim_world.get_settings().synchronous_mode:
            print("WARNING: You are currently in asynchronous mode and could "
                  "experience some issues with the traffic simulation")

        display = pygame.display.set_mode(
            (args.width, args.height),
            pygame.HWSURFACE | pygame.DOUBLEBUF)
        display.fill((0,0,0))
        pygame.display.flip()

        hud = HUD(args.width, args.height)
        world = World(sim_world, hud, args)
        controller = KeyboardControl(world, args.autopilot)

        five_secs_tick = 0
        Npc_data_idx = FIRST_EFFECTIVE_DATA_IDX
        global START_INJECT
        current_state = automata_name_list[0]
        action = 0
        if args.sync:
            sim_world.tick()
        else:
            sim_world.wait_for_tick()
        ego_vehicle = world.player
        time.sleep(1)
        zero_velocity_vector = carla.Vector3D(0,0,0)
        ego_vehicle.set_target_velocity(zero_velocity_vector)
        ego_vehicle.enable_constant_velocity(zero_velocity_vector)

        dy_velocity_vector = carla.Vector3D(5.6,0,0)
        velocity_vector = carla.Vector3D(10,0,0)
        npc_velocity_vector = carla.Vector3D(5,0,0)

        normal_vehicle = sim_world.get_blueprint_library().filter("vehicle.nissan.micra")
        print(ego_vehicle.get_transform())
        init_location = ego_vehicle.get_location()
        init_transform = ego_vehicle.get_transform()
        next_location = init_location
        next_location.x = next_location.x - 50 - CAR_ERROR
        next_location.z = next_location.z + 3
        npc_spawn_point = carla.Transform(next_location,init_transform.rotation)
        print(npc_spawn_point)
        ret = sim_world.try_spawn_actor(random.choice(normal_vehicle), npc_spawn_point)
        time.sleep(1)
        if ret == None:
            print("spawn npc car false")
        else:
            print("spawn npc car true")
            # ret.set_enable_gravity(True)
            # ret.set_simulate_physics(True)
            ret.set_target_velocity(zero_velocity_vector)
            physics_control = ret.get_physics_control()
            physics_control.use_sweep_wheel_collision = True
            ret.apply_physics_control(physics_control)
            ret.enable_constant_velocity(zero_velocity_vector)
            
        static_obs = set_static_obstacle(ego_vehicle,sim_world)
        dynamic_car = set_dynamic_obstacle(ego_vehicle,sim_world)
        time.sleep(1)
        clock = pygame.time.Clock()
        
        ego_vehicle.set_target_velocity(zero_velocity_vector)
        ego_vehicle.enable_constant_velocity(zero_velocity_vector)
        
        dynamic_car.apply_control(carla.WalkerControl(carla.Vector3D(-1.0,0,0), 0, False))
        # dynamic_car.set_target_velocity(zero_velocity_vector)
        # dynamic_car.enable_constant_velocity(zero_velocity_vector)
        # ego_vehicle.set_enable_gravity(True)
        # ego_vehicle.set_simulate_physics(True)
        
        #world.tick(clock)
        time.sleep(4)
        
        
        ego_vehicle.set_target_velocity(velocity_vector)
        ego_vehicle.enable_constant_velocity(velocity_vector)
        ret.set_target_velocity(npc_velocity_vector)
        ret.enable_constant_velocity(npc_velocity_vector)
        dynamic_velocity = set_dynamic_obstacle_velocity(1)
        print('dynamic_velocity = ', dynamic_velocity)
        dynamic_car.apply_control(carla.WalkerControl(carla.Vector3D(-1.0,0,0), dynamic_velocity.x, False))
        # dynamic_car.set_target_velocity(set_dynamic_obstacle_velocity(1))
        # dynamic_car.enable_constant_velocity(set_dynamic_obstacle_velocity(1))
        
        #time.sleep(4)
        #
        total_sample_time = len(automata_dict['state1'])
        print(f'total_sample_time = {total_sample_time}')
        sample_idx = 0

        a_ego = 0
        while True:
            if args.sync:
                sim_world.tick()
            
            
            clock.tick_busy_loop(100)
            if controller.parse_events(client, world, clock, args.sync):
                return
            world.tick(clock, action)
            world.render(display)
            pygame.display.flip()
            tick_time = world.get_tick_time()
            # print(tick_time)
            # print('sample_idx = ', sample_idx)
            new_ego_velocity = velocity_vector.x + a_ego * 0.01
            # print(velocity_vector.x, a_ego, time_interval, new_ego_velocity)
            velocity_vector = carla.Vector3D(new_ego_velocity,0,0)
            new_ego_velocity_vector = carla.Vector3D(new_ego_velocity,0,0)
            ego_vehicle.set_target_velocity(new_ego_velocity_vector)
            ego_vehicle.enable_constant_velocity(new_ego_velocity_vector)

            if sample_idx < total_sample_time:
                if tick_time == automata_dict['state0'][sample_idx] * 100:
                    next_state = automata_name_list[1]
                    print(f'-----------------TRANS FROM {current_state} TO {next_state}-----------------:{tick_time}')
                    
                    current_state = next_state
                    sample_frame_idx = 0
                    for time_idx in range(len(info['t'])):
                        if info['t'][time_idx] == automata_dict['state0'][sample_idx]:
                            sample_frame_idx = time_idx
                            break
                    print('-----------------FINISH SAMPLING-----------------')

            if tick_time == round(automata_dict['state1'][sample_idx] * 100, 0):
                next_state = automata_name_list[2]
                print(f'-----------------TRANS FROM {current_state} TO {next_state}-----------------:{tick_time}')
                print(f'sample_frame_idx = {sample_frame_idx}')
                dd = calculate_dd(sample_frame_idx)
                danger = compute_danger(sample_frame_idx, init_location, ego_vehicle.get_location(), \
                                        static_obs.get_location(), dynamic_car.get_location())
                print(f'dd = {dd}, danger = {danger}')
                a_ego = calculate_acceleration(danger, sample_frame_idx, dd)
                print(f'a_ego = {a_ego}')
                action = calculate_action(a_ego)
                current_state = next_state
            
            if tick_time == round(automata_dict['state2'][sample_idx] * 100, 0):
                next_state = automata_name_list[0]
                print(f'-----------------TRANS FROM {current_state} TO {next_state}-----------------')
                current_state = next_state

            if START_INJECT == True:
                for time_idx in range(len(info['t'])):
                    if round(float(info['t'][time_idx]) * 100, 0) == tick_time:
                        # print(f'set_ego_v and dynamic_v, {tick_time}')
                        if dynamic_car is not None and time_idx < len(info['RandomActorX_env']) - 1:
                            dynamic_velocity = set_dynamic_obstacle_velocity(time_idx)
                            
                            last_dynamic_velocity = dynamic_velocity
                        else:
                            dynamic_velocity = last_dynamic_velocity
                        # print('dynamic_velocity = ', dynamic_velocity)
                        
                        dynamic_car.apply_control(carla.WalkerControl(carla.Vector3D(-1.0,0,0), dynamic_velocity.x, False))


                        # print('ego_velocity = ', new_ego_velocity)

                        new_npc_velocity = float(info['v_env'][time_idx])
                        new_npc_velocity_vector = carla.Vector3D(new_npc_velocity,0,0)
                        ret.set_target_velocity(new_npc_velocity_vector)
                        ret.enable_constant_velocity(new_npc_velocity_vector)
                        break


            if world.hud.is_collision == True:
                ego_vehicle.enable_constant_velocity(zero_velocity_vector)
                ret.enable_constant_velocity(zero_velocity_vector)
                if dynamic_car is not None:
                    dynamic_car.enable_constant_velocity(zero_velocity_vector)
                print(ego_vehicle.get_location())
                print(dynamic_car.get_location())
                print(ret.get_location())
                time.sleep(3)
                break

    finally:
        danger_car_list = sim_world.get_actors().filter("vehicle.nissan.micra")
        dynamic_car_list = sim_world.get_actors().filter("walker.pedestrian.0001")
        static_obstacle_list = sim_world.get_actors().filter("static.prop.barrel")
        
        
        client.apply_batch([carla.command.DestroyActor(x) for x in danger_car_list])
        client.apply_batch([carla.command.DestroyActor(x) for x in dynamic_car_list])
        client.apply_batch([carla.command.DestroyActor(x) for x in static_obstacle_list])
        
        if original_settings:
            sim_world.apply_settings(original_settings)

        if (world and world.recording_enabled):
            client.stop_recorder()

        if world is not None:
            world.destroy()

        pygame.quit()


def set_dynamic_obstacle_velocity(time_idx):
    current_dx = float(info['RandomActorX_env'][time_idx])
    next_dx = float(info['RandomActorX_env'][time_idx + 1])
    time_interval = float(info['t'][time_idx + 1]) - float(info['t'][time_idx])
    new_velocity = (next_dx - current_dx) / time_interval
    return carla.Vector3D(new_velocity,0,0)

def set_dynamic_obstacle(ego_vehicle,world):
    x_offset = float(info['RandomActorX_env'][1])
    y_offset = float(info['RandomActorY_env'][1])
    # print(x_offset)
    # print(y_offset)
    init_location = ego_vehicle.get_location()
    init_transform = ego_vehicle.get_transform()
    
    dynamic_obs_location = init_location
    dynamic_obs_location.x = dynamic_obs_location.x - x_offset - PEDESTRIAN_ERROR ### here changes, according to different situation
    dynamic_obs_location.y = dynamic_obs_location.y + y_offset
    dynamic_obs_location.z = dynamic_obs_location.z + 4
    dynamic_obs_rotation = init_transform.rotation
    # dynamic_obs_rotation.yaw = dynamic_obs_rotation.yaw + 90
    dynamic_obs_spawn_point = carla.Transform(dynamic_obs_location,dynamic_obs_rotation)
        
    dynamic_obstacle = world.get_blueprint_library().filter("walker.pedestrian.0001")
    
    bp = random.choice(dynamic_obstacle)
    bp.set_attribute('is_invincible', 'false')
    dynamic_ret = world.try_spawn_actor(bp, dynamic_obs_spawn_point)
    if dynamic_ret == None:
        print("spawn dynamic obs false")
        return None
    else:
        dynamic_ret.set_enable_gravity(True)
        dynamic_ret.set_simulate_physics(True)
        print("spawn dynamic obs true")
        print(dynamic_obs_spawn_point)
        return dynamic_ret
    

def set_static_obstacle(ego_vehicle,world):
    x_offset = float(info['staticActorX_env'][1])
    y_offset = float(info['staticActorY_env'][1])

    
    init_location = ego_vehicle.get_location()
    init_transform = ego_vehicle.get_transform()
    static_obs_location = init_location

    
    static_obs_location.x = static_obs_location.x - x_offset - STATIC_OBS_ERROR

    static_obs_location.y = static_obs_location.y + y_offset
    static_obs_location.z = static_obs_location.z + 2
    static_obs_spawn_point = carla.Transform(static_obs_location,init_transform.rotation)
        
    static_obstacle = world.get_blueprint_library().filter("static.prop.barrel")
    static_ret = world.try_spawn_actor(random.choice(static_obstacle), static_obs_spawn_point)
    if static_ret == None:
        print("spawn static obstacle false")
    else:
        static_ret.set_enable_gravity(True)
        static_ret.set_simulate_physics(True)
        print("spawn staic obstacle true")
    print(static_obs_spawn_point)
    return static_ret

def modify_signal_env():
    info['signal_env'] = list()
    info['signal_env'].append(-1)
    info['signal_env'].append(1)

def calculate_dd(sample_frame_idx):
    return float(info['x_env'][sample_frame_idx]) - float(info['x_ego'][sample_frame_idx]) + \
        float(info['err'][sample_frame_idx])


def calculate_static_danger(sample_frame_idx):
    x_danger = DANGER_LIMIT - \
        abs(float(info['staticActorX_env'][sample_frame_idx]) - float(info['x_ego'][sample_frame_idx]))
    y_danger = DANGER_LIMIT - \
        abs(float(info['staticActorY_env'][sample_frame_idx]) - float(info['y_ego'][sample_frame_idx]))
    lhs = 0
    rhs = 0
    if x_danger > 0:    
        lhs = 1
    else:
        lhs = 0
    if y_danger > 0:    
        rhs = 1
    else:
        rhs = 0
    return lhs*rhs
    
def calculate_dynamic_danger(sample_frame_idx):
    x_danger = DANGER_LIMIT - \
        abs(float(info['RandomActorX_env'][sample_frame_idx]) - float(info['x_ego'][sample_frame_idx]))
    y_danger = DANGER_LIMIT - \
        abs(float(info['RandomActorY_env'][sample_frame_idx]) - float(info['y_ego'][sample_frame_idx]))
    lhs = 0
    rhs = 0
    if x_danger > 0:    
        lhs = 1
    else:
        lhs = 0
    if y_danger > 0:    
        rhs = 1
    else:
        rhs = 0
    return lhs*rhs

def calculate_signal_danger(sample_frame_idx):
    # x_danger = 0.5 - abs(info['restrictSignalAreaX_env'][SAMPLE_FRAME_IDX] - info['x_ego'][SAMPLE_FRAME_IDX])
    # y_danger = 0.5 - abs(info['RandomActorY_env'][SAMPLE_FRAME_IDX] - info['y_ego'][SAMPLE_FRAME_IDX])
 
    x_danger = DANGER_LIMIT - \
        abs(float(info['restrictSignalAreaX_envsample'][sample_frame_idx]) - float(info['x_ego'][sample_frame_idx]))
    y_danger = float(info['signal_envsample'][sample_frame_idx]) - 0.5
    lhs = 0
    rhs = 0
    if x_danger > 0:    
        lhs = 1
    else:
        lhs = 0
    if y_danger > 0:    
        rhs = 1
    else:
        rhs = 0
    return lhs*rhs
"""
danger:=((sign(0.5 - (abs staticActorX_envsample - x_egosample)) * sign((0.5) - (abs (staticActorY_envsample - y_egosample))))) * (1) 
+ (signEq(-((sign((0.5) - (abs (staticActorX_envsample - x_egosample))) * sign((0.5) - (abs (staticActorY_envsample - y_egosample))))))*(sign((0.5) - (abs (RandomActorX_envsample - x_egosample))) * sign((0.5) - (abs (RandomActorY_envsample - y_egosample))))) * (1) + (signEq(-(signEq(-((sign((0.5) - (abs (staticActorX_envsample - x_egosample))) * sign((0.5) - (abs (staticActorY_envsample - y_egosample))))))*(sign((0.5) - (abs (RandomActorX_envsample - x_egosample))) * sign((0.5) - (abs (RandomActorY_envsample - y_egosample))))))*(sign((0.5) -
 (abs (restrictSignalAreaX_envsample - x_egosample))) * sign((signal_envsample) - (0.5)))) * (1) + 
 (signEq(-(signEq(-(signEq(-((sign((0.5) - (abs (staticActorX_envsample - x_egosample))) * sign((0.5) - (abs (staticActorY_envsample - y_egosample))))))*(sign((0.5) - (abs (RandomActorX_envsample - x_egosample))) * sign((0.5) - (abs (RandomActorY_envsample - y_egosample))))))*(sign((0.5) - (abs (restrictSignalAreaX_envsample - x_egosample))) * sign((signal_envsample) - (0.5)))))*(sign(sign(sign(sign((0.5) - (abs (restrictRailCrossAreaXmin_envsample - x_egosample))) + sign((0.5) - (abs (restrictRailCrossAreaXmax_envsample - x_egosample)))) + sign((0.5) - (abs (restrictRailCrossAreaYmin_envsample - y_egosample)))) + sign((0.5) - (abs (restrictRailCrossAreaYmax_envsample - y_egosample)))) * sign((railSignal_envsample) - (0.5)))) * (1) + (signEq(-(signEq(-(signEq(-(signEq(-((sign((0.5) - (abs (staticActorX_envsample - x_egosample))) * sign((0.5) - (abs (staticActorY_envsample - y_egosample))))))*(sign((0.5) - (abs (RandomActorX_envsample - x_egosample))) * sign((0.5) - (abs (RandomActorY_envsample - y_egosample))))))*(sign((0.5) - (abs (restrictSignalAreaX_envsample - x_egosample))) * sign((signal_envsample) - (0.5)))))*(sign(sign(sign(sign((0.5) - (abs (restrictRailCrossAreaXmin_envsample - x_egosample))) + sign((0.5) - (abs (restrictRailCrossAreaXmax_envsample - x_egosample)))) + sign((0.5) - (abs (restrictRailCrossAreaYmin_envsample - y_egosample)))) + sign((0.5) - (abs (restrictRailCrossAreaYmax_envsample - y_egosample)))) * sign((railSignal_envsample) - (0.5)))))*sign(sign(sign(sign((0.5) - (abs (restrictParkAreaXmin_envsample - x_egosample))) + sign((0.5) - (abs (restrictParkAreaXmax_envsample - x_egosample)))) + sign((0.5) - (abs (restrictParkAreaYmin_envsample - y_egosample)))) + sign((0.5) - (abs (restrictParkAreaYmax_envsample - y_egosample))))) * (1) + (signEq(-(signEq(-(signEq(-(signEq(-(signEq(-((sign((0.5) - (abs (staticActorX_envsample - x_egosample))) * sign((0.5) - (abs (staticActorY_envsample - y_egosample))))))*(sign((0.5) - (abs (RandomActorX_envsample - x_egosample))) * sign((0.5) - (abs (RandomActorY_envsample - y_egosample))))))*(sign((0.5) - (abs (restrictSignalAreaX_envsample - x_egosample))) * sign((signal_envsample) - (0.5)))))*(sign(sign(sign(sign((0.5) - (abs (restrictRailCrossAreaXmin_envsample - x_egosample))) + sign((0.5) - (abs (restrictRailCrossAreaXmax_envsample - x_egosample)))) + sign((0.5) - (abs (restrictRailCrossAreaYmin_envsample - y_egosample)))) + sign((0.5) - (abs (restrictRailCrossAreaYmax_envsample - y_egosample)))) * sign((railSignal_envsample) - (0.5)))))*sign(sign(sign(sign((0.5) - (abs (restrictParkAreaXmin_envsample - x_egosample))) + sign((0.5) - (abs (restrictParkAreaXmax_envsample - x_egosample)))) + sign((0.5) - (abs (restrictParkAreaYmin_envsample - y_egosample)))) + sign((0.5) - (abs (restrictParkAreaYmax_envsample - y_egosample))))))*sign(sign(sign(sign((0.5) - (abs (restrictUturnAreaXmin_envsample - x_egosample))) + sign((0.5) - (abs (restrictUturnAreaXmax_envsample - x_egosample)))) + sign((0.5) - (abs (restrictUturnAreaYmin_envsample - y_egosample)))) + sign((0.5) - (abs (restrictUturnAreaYmax_envsample - y_egosample))))) * (1) + (signEq(-(signEq(-(signEq(-(signEq(-(signEq(-(signEq(-((sign((0.5) - (abs (staticActorX_envsample - x_egosample))) * sign((0.5) - (abs (staticActorY_envsample - y_egosample))))))*(sign((0.5) - (abs (RandomActorX_envsample - x_egosample))) * sign((0.5) - (abs (RandomActorY_envsample - y_egosample))))))*(sign((0.5) - (abs (restrictSignalAreaX_envsample - x_egosample))) * sign((signal_envsample) - (0.5)))))*(sign(sign(sign(sign((0.5) - (abs (restrictRailCrossAreaXmin_envsample - x_egosample))) + sign((0.5) - (abs (restrictRailCrossAreaXmax_envsample - x_egosample)))) + sign((0.5) - (abs (restrictRailCrossAreaYmin_envsample - y_egosample)))) + sign((0.5) - (abs (restrictRailCrossAreaYmax_envsample - y_egosample)))) * sign((railSignal_envsample) - (0.5)))))*sign(sign(sign(sign((0.5) - (abs (restrictParkAreaXmin_envsample - x_egosample))) + sign((0.5) - (abs (restrictParkAreaXmax_envsample - x_egosample)))) + sign((0.5) - (abs (restrictParkAreaYmin_envsample - y_egosample)))) + sign((0.5) - (abs (restrictParkAreaYmax_envsample - y_egosample))))))*sign(sign(sign(sign((0.5) - (abs (restrictUturnAreaXmin_envsample - x_egosample))) + sign((0.5) - (abs (restrictUturnAreaXmax_envsample - x_egosample)))) + sign((0.5) - (abs (restrictUturnAreaYmin_envsample - y_egosample)))) + sign((0.5) - (abs (restrictUturnAreaYmax_envsample - y_egosample))))))) * (0)
"""


def check_isexistence(key):
    def val(key):
        return float(info[key][1])
    if val(key) == 0:
        return False
    else:
        return True 

def sign(a):
    return 1 if a > 0 else 0

def signeq(a):
    return 1 if a >= 0 else 0

def compute_danger(sample_frame_idx, init_ego_pos, ego_pos, static_obs_pos, random_actor_pos):
    def val(key):
        return float(info[key][sample_frame_idx])
    """
    t =0.04 , sample , x_env -> x_envsample

    t =0.14 , calculate, a = ....;

    t = 0.1 sample, a = ....
    t = 0.1 , control 
    """

    A = sign(0.5 - abs(static_obs_pos.x - ego_pos.x)) * \
        sign(0.5 - abs(static_obs_pos.y - ego_pos.y))
    
    B = sign(0.5 - abs(random_actor_pos.x - ego_pos.x)) * \
        sign(0.5 - abs(random_actor_pos.y - ego_pos.y))

    C = sign(0.5 - abs((init_ego_pos.x - val('restrictSignalAreaX_env')) - ego_pos.x)) * \
        sign(val('signal_env') - 0.5)

    # A = sign(0.5 - abs(val('staticActorX_env') - val('x_ego'))) * \
    #     sign(0.5 - abs(val('staticActorY_env') - val('y_ego')))

    # B = sign(0.5 - abs(val('RandomActorX_env') - val('x_ego'))) * \
    #     sign(0.5 - abs(val('RandomActorY_env') - val('y_ego')))

    # C = sign(0.5 - abs(val('restrictSignalAreaX_env') - val('x_ego'))) * \
    #     sign(val('signal_env') - 0.5)

    if not check_isexistence('restrictRailCrossAreaXmin_env') and not check_isexistence('restrictRailCrossAreaXmax_env') and \
        not check_isexistence('restrictRailCrossAreaYmin_env') and not check_isexistence('restrictRailCrossAreaYmax_env'):
        D = sign(
            sign(
                sign(
                    sign(0.5 - abs(val('restrictRailCrossAreaXmin_env') - val('x_ego'))) +
                    sign(0.5 - abs(val('restrictRailCrossAreaXmax_env') - val('x_ego')))
                ) +
                sign(0.5 - abs(val('restrictRailCrossAreaYmin_env') - val('y_ego')))
            ) +
            sign(0.5 - abs(val('restrictRailCrossAreaYmax_env') - val('y_ego')))
        ) * sign(val('railSignal_env') - 0.5)
    else:
        D = sign(
            sign(
                sign(
                    sign(0.5 - abs((init_ego_pos.x - val('restrictRailCrossAreaXmin_env')) - ego_pos.x)) +
                    sign(0.5 - abs((init_ego_pos.x - val('restrictRailCrossAreaXmax_env')) - ego_pos.x))
                ) +
                sign(0.5 - abs((init_ego_pos.y - val('restrictRailCrossAreaYmin_env')) - ego_pos.y))
            ) +
            sign(0.5 - abs((init_ego_pos.y - val('restrictRailCrossAreaYmax_env')) - ego_pos.y))
        ) * sign(val('railSignal_env') - 0.5)

    if not check_isexistence('restrictParkAreaXmin_env') and not check_isexistence('restrictParkAreaXmax_env') and \
        not check_isexistence('restrictParkAreaYmin_env') and not check_isexistence('restrictParkAreaYmax_env'):
        E = sign(
            sign(
                sign(
                    sign(0.5 - abs(val('restrictParkAreaXmin_env') - val('x_ego'))) +
                    sign(0.5 - abs(val('restrictParkAreaXmax_env') - val('x_ego')))
                ) +
                sign(0.5 - abs(val('restrictParkAreaYmin_env') - val('y_ego')))
            ) +
            sign(0.5 - abs(val('restrictParkAreaYmax_env') - val('y_ego')))
        )
    else:
        E = sign(
            sign(
                sign(
                    sign(0.5 - abs((init_ego_pos.x - val('restrictParkAreaXmin_env')) - ego_pos.x)) +
                    sign(0.5 - abs((init_ego_pos.x - val('restrictParkAreaXmax_env')) - ego_pos.x))
                ) +
                sign(0.5 - abs((init_ego_pos.y - val('restrictParkAreaYmin_env')) - ego_pos.y))
            ) +
            sign(0.5 - abs((init_ego_pos.y - val('restrictParkAreaYmax_env')) - ego_pos.y))
        )

    if not check_isexistence('restrictUturnAreaXmin_env') and not check_isexistence('restrictUturnAreaXmax_env') and \
        not check_isexistence('restrictUturnAreaYmin_env') and not check_isexistence('restrictUturnAreaYmax_env'):
        F = sign(
            sign(
                sign(
                    sign(0.5 - abs(val('restrictUturnAreaXmin_env') - val('x_ego'))) +
                    sign(0.5 - abs(val('restrictUturnAreaXmax_env') - val('x_ego')))
                ) +
                sign(0.5 - abs(val('restrictUturnAreaYmin_env') - val('y_ego')))
            ) +
            sign(0.5 - abs(val('restrictUturnAreaYmax_env') - val('y_ego')))
        )
    else:
        F = sign(
            sign(
                sign(
                    sign(0.5 - abs((init_ego_pos.x - val('restrictUturnAreaXmin_env')) - ego_pos.x)) +
                    sign(0.5 - abs((init_ego_pos.x - val('restrictUturnAreaXmax_env')) - ego_pos.x))
                ) +
                sign(0.5 - abs((init_ego_pos.y - val('restrictUturnAreaYmin_env')) - ego_pos.y))
            ) +
            sign(0.5 - abs((init_ego_pos.y - val('restrictUturnAreaYmax_env')) - ego_pos.y))
        )

    danger = (
        A +
        signeq(-A) * B +
        signeq(-signeq(-A) * B) * C +
        signeq(-signeq(-signeq(-A) * B) * C) * D +
        signeq(-signeq(-signeq(-signeq(-A) * B) * C) * D) * E +
        signeq(-signeq(-signeq(-signeq(-signeq(-A) * B) * C) * D) * E) * F * 0
    )

    return danger

def calculate_neg_five_acc(danger,sample_frame_idx):
    if danger > 0:
        standard_acc = get_config_value("Deacceleration", -3)
        print(f'standard_acc = {standard_acc}')
        modify_acc = 10 * 0.01 * float(info['friction'][sample_frame_idx]) * \
            math.cos(float(info['slope'][sample_frame_idx]))
        return standard_acc - modify_acc
    else:
        return 0

def calculate_pos_two_acc(danger,dd,sample_frame_idx):
    standard_acc = get_config_value("Acceleration", 3)
    modify_acc = 10 * 0.01 * float(info['frictionsample'][sample_frame_idx]) * \
        math.cos(float(info['slopesample'][sample_frame_idx]))
    return (signeq(-(sign(danger)))* sign(dd - SAFETY_DISTANCE)) * (standard_acc - modify_acc)


def calculate_neg_two_acc(danger,dd,sample_frame_idx):
    standard_acc = get_config_value("Deacceleration", -3)
    modify_acc = 10 * 0.01 * float(info['frictionsample'][sample_frame_idx]) * \
        math.cos(float(info['slopesample'][sample_frame_idx]))
            
    return (signeq(-(sign(danger))) * signeq(-sign(dd - SAFETY_DISTANCE))) * (standard_acc - modify_acc)


"""
contl_aego:=(sign((danger) - (0))) * (-3 - 10 * 0.01 * frictionsample * cos_slope) \
    + (signEq(-(sign(danger )))*sign(dd - 30)) * (3 - 10 * 0.01 * frictionsample * cos_slope) \
        + (signEq(-(signEq(-(sign(danger)))*sign(dd - 30)))) * (-3 - 10 * 0.01 * frictionsample * cos_slope)
"""
"""
contl_aego:=(sign(danger - 0)) * (-3 - 10 * 0.01 * frictionsample * cos_slope) \
    + (signEq(-(sign(danger)))*sign((dd) - (30))) * (3 - 10 * 0.01 * frictionsample * cos_slope) \
        + (signEq(-(signEq(-sign(danger))*sign((dd) - (30))))) * (-3 - 10 * 0.01 * frictionsample * cos_slope)
"""
"""
(signEq(-(signEq(-(sign((danger) - (0))))*sign((dd) - (30))))) * (-3 - 10 * 0.01 * frictionsample * cos_slope)
(signEq(-(sign((danger) - (0)))) * signEq(-(sign((dd) - (30))))) * (-3 - 10 * 0.01 * frictionsample * cos_slope)
(signEq(-(sign(danger))) * signEq(-(sign(dd - 30)))) * (-3 - 10 * 0.01 * frictionsample * cos_slope)
"""
def calculate_acceleration(danger,sample_frame_idx,dd):
    neg_five_acceleration = calculate_neg_five_acc(danger,sample_frame_idx)
    two_acceleration = calculate_pos_two_acc(danger, dd,sample_frame_idx)
    neg_two_acceleration = calculate_neg_two_acc(danger,dd,sample_frame_idx)
    print(f'neg_five_acceleration = {neg_five_acceleration}, two_acceleration = {two_acceleration}, neg_two_acceleration = {neg_two_acceleration}')
    total_acc = neg_five_acceleration + two_acceleration + neg_two_acceleration
    return total_acc

def calculate_action(ego_acc):
    if ego_acc > 0:
        return 1
    elif ego_acc == 0:
        return 0
    else:
        return -1

def calculate_forbidden_state(cycle_frame_idx,action):
    if action != 1:
        print("not in forbidden state")
    else:
        distance_to_tl = abs(float(info['restrictSignalAreaX_env'][cycle_frame_idx]) - \
            float(info['x_ego'][cycle_frame_idx]))
        tl_color = float(info['signal_env'][cycle_frame_idx])
        if distance_to_tl < 0.05 and tl_color > 0.5:
            print('in forbidden state')
        else:
            print('not in forbidden state')


# ==============================================================================
# -- main() --------------------------------------------------------------------
# ==============================================================================


def main():
    argparser = argparse.ArgumentParser(
        description='CARLA Manual Control Client')
    argparser.add_argument(
        '-v', '--verbose',
        action='store_true',
        dest='debug',
        help='print debug information')
    argparser.add_argument(
        '--host',
        metavar='H',
        default='172.17.0.1',
        help='IP of the host server (default: 172.17.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '-a', '--autopilot',
        action='store_true',
        help='enable autopilot')
    argparser.add_argument(
        '--res',
        metavar='WIDTHxHEIGHT',
        default='1280x720',
        help='window resolution (default: 1280x720)')
    argparser.add_argument(
        '--filter',
        metavar='PATTERN',
        default='vehicle.lincoln.mkz_2017',
        help='actor filter (default: "vehicle.lincoln.mkz_2017")')
    argparser.add_argument(
        '--generation',
        metavar='G',
        default='2',
        help='restrict to certain actor generation (values: "1","2","All" - default: "2")')
    argparser.add_argument(
        '--rolename',
        metavar='NAME',
        default='hero',
        help='actor role name (default: "hero")')
    argparser.add_argument(
        '--gamma',
        default=2.2,
        type=float,
        help='Gamma correction of the camera (default: 2.2)')
    argparser.add_argument(
        '--sync',
        action='store_true',
        help='Activate synchronous mode execution')
    args = argparser.parse_args()

    args.width, args.height = [int(x) for x in args.res.split('x')]

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)

    logging.info('listening to server %s:%s', args.host, args.port)

    print(__doc__)

    for key in key_list:
        info[key] = list()
    idx = 0
    row_idx = 0
    with open(path + 'result.csv', 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            data = row[0]
            if idx == 0:
                
                data_info = data.split("\t")
                for word in data_info:
                    for key in key_list:
                        if key == word:
                            info[key].append(row_idx)
                    row_idx += 1
            else:
                data_info = data.split("\t")
                for key in key_list:
                    info[key].append(data_info[info[key][0]])
            idx += 1
    file.close()
    
    t_list = list()
    modify_t_idx = 0
    for key in key_list:
        if key == 't':
            for data in info[key]:
                t_list.append(float(data) + modify_t_idx * 3)
                if float(data) == 3:
                    modify_t_idx += 1
            break
    info['t'] = t_list
    
    for name in automata_name_list:
        automata_dict[name] = list()
    line_idx = 0
    timestep_info = open(path + 'TimePath.txt', 'r')
    for line in timestep_info:
        if line_idx == 1:
            line_info = line.split('\n')[0].split(' ')
            data_idx = 0
            accumulate_time = 0
            for time_stay in line_info:
                if time_stay == '' or time_stay == '0':
                    continue
                float_time_stay = float(time_stay)
                accumulate_time += float_time_stay
                if data_idx % len(automata_name_list) == 0:
                    automata_dict[automata_name_list[0]].append(accumulate_time)
                elif data_idx % len(automata_name_list) == 1:
                    automata_dict[automata_name_list[1]].append(accumulate_time)
                elif data_idx % len(automata_name_list) == 2:
                    automata_dict[automata_name_list[2]].append(accumulate_time)
                
                data_idx += 1
        line_idx += 1
        if line_idx == 2: break
    timestep_info.close()
    parse_acceleration_config(path + 'acceleration_config.txt')
    try:

        game_loop(args)

    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')


if __name__ == '__main__':

    main()
