# Copyright (c) # Copyright (c) 2018-2020 CVC.
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.


""" This module implements an agent that roams around a track following random
waypoints and avoiding other vehicles. The agent also responds to traffic lights,
traffic signs, and has different possible configurations. """

import random
import numpy as np
import carla
from basic_agent import BasicAgent
from local_planner import RoadOption
from behavior_types import Cautious, Aggressive, Normal

from misc import get_speed, positive, is_within_distance, compute_distance


class BehaviorAgent(BasicAgent):
    """
    BehaviorAgent implements an agent that navigates scenes to reach a given
    target destination, by computing the shortest possible path to it.
    This agent can correctly follow traffic signs, speed limitations,
    traffic lights, while also taking into account nearby vehicles. Lane changing
    decisions can be taken by analyzing the surrounding environment such as tailgating avoidance.
    Adding to these are possible behaviors, the agent can also keep safety distance
    from a car in front of it by tracking the instantaneous time to collision
    and keeping it in a certain range. Finally, different sets of behaviors
    are encoded in the agent, from cautious to a more aggressive ones.
    """

    def __init__(self, vehicle, behavior='normal', opt_dict={}, map_inst=None, grp_inst=None):
        """
        Constructor method.

            :param vehicle: actor to apply to local planner logic onto
            :param behavior: type of agent to apply
        """

        super().__init__(vehicle, opt_dict=opt_dict, map_inst=map_inst, grp_inst=grp_inst)
        self._look_ahead_steps = 0

        # Vehicle information
        self._speed = 0
        self._speed_limit = 0
        self._direction = None
        self._incoming_direction = None
        self._incoming_waypoint = None
        self._min_speed = 5
        self._behavior = None
        self._sampling_resolution = 4.5
        self._overtaking = None

        # Parameters for agent behavior
        if behavior == 'cautious':
            self._behavior = Cautious()

        elif behavior == 'normal':
            self._behavior = Normal()

        elif behavior == 'aggressive':
            self._behavior = Aggressive()

    def _update_information(self):
        """
        This method updates the information regarding the ego
        vehicle based on the surrounding world.
        """
        self._speed = get_speed(self._vehicle)
        print("velocità del veicolo ", self._speed)
        self._speed_limit = self._vehicle.get_speed_limit()
        self._local_planner.set_speed(self._speed_limit)
        self._direction = self._local_planner.target_road_option
        if self._direction is None:
            self._direction = RoadOption.LANEFOLLOW

        self._look_ahead_steps = int((self._speed_limit) / 10)

        self._incoming_waypoint, self._incoming_direction = self._local_planner.get_incoming_waypoint_and_direction(
            steps=self._look_ahead_steps)
        if self._incoming_direction is None:
            self._incoming_direction = RoadOption.LANEFOLLOW

    def traffic_light_manager(self):
        """
        This method is in charge of behaviors for red lights.
        """
        actor_list = self._world.get_actors()
        lights_list = actor_list.filter("*traffic_light*")
        affected, _ = self._affected_by_traffic_light(lights_list)

        return affected

    def _tailgating(self, waypoint, vehicle_list):
        """
        This method is in charge of tailgating behaviors.

            :param location: current location of the agent
            :param waypoint: current waypoint of the agent
            :param vehicle_list: list of all the nearby vehicles
        """

        left_turn = waypoint.left_lane_marking.lane_change
        right_turn = waypoint.right_lane_marking.lane_change

        left_wpt = waypoint.get_left_lane()
        right_wpt = waypoint.get_right_lane()

        behind_vehicle_state, behind_vehicle, _ = self._vehicle_obstacle_detected(vehicle_list, max(
            self._behavior.min_proximity_threshold, self._speed_limit / 2), up_angle_th=180, low_angle_th=160)[0]

        if behind_vehicle_state and self._speed < get_speed(behind_vehicle):
            if (right_turn == carla.LaneChange.Right or right_turn ==
                carla.LaneChange.Both) and waypoint.lane_id * right_wpt.lane_id > 0 and right_wpt.lane_type == carla.LaneType.Driving:
                new_vehicle_state, _, _ = self._vehicle_obstacle_detected(vehicle_list, max(
                    self._behavior.min_proximity_threshold, self._speed_limit / 2), up_angle_th=180, lane_offset=1)[0]
                if not new_vehicle_state:
                    print("Tailgating, moving to the right!")
                    end_waypoint = self._local_planner.target_waypoint
                    self._behavior.tailgate_counter = 200
                    self.set_destination(end_waypoint.transform.location,
                                         right_wpt.transform.location)
            elif left_turn == carla.LaneChange.Left and waypoint.lane_id * left_wpt.lane_id > 0 and left_wpt.lane_type == carla.LaneType.Driving:
                new_vehicle_state, _, _ = self._vehicle_obstacle_detected(vehicle_list, max(
                    self._behavior.min_proximity_threshold, self._speed_limit / 2), up_angle_th=180, lane_offset=-1)[0]
                if not new_vehicle_state:
                    print("Tailgating, moving to the left!")
                    end_waypoint = self._local_planner.target_waypoint
                    self._behavior.tailgate_counter = 200
                    self.set_destination(end_waypoint.transform.location,
                                         left_wpt.transform.location)

    def collision_and_car_avoid_manager(self, waypoint):
        """
        This module is in charge of warning in case of a collision
        and managing possible tailgating chances.

            :param location: current location of the agent
            :param waypoint: current waypoint of the agent
            :return vehicle_state: True if there is a vehicle nearby, False if not
            :return vehicle: nearby vehicle
            :return distance: distance to nearby vehicle
        """
        #print(self._world.get_actors())
        vehicle_list = self._world.get_actors().filter("*vehicle*")

        def dist(v):
            return v.get_location().distance(waypoint.transform.location)

        vehicle_list = [v for v in vehicle_list if dist(v) < 45 and v.id != self._vehicle.id]

        print("direzione ", self._direction)

        if self._direction == RoadOption.CHANGELANELEFT:
            vehicle_state, vehicle, distance = self._vehicle_obstacle_detected(
                vehicle_list, max(
                    self._behavior.min_proximity_threshold, self._speed_limit / 2), up_angle_th=180, lane_offset=-1)[0]
        elif self._direction == RoadOption.CHANGELANERIGHT:
            vehicle_state, vehicle, distance = self._vehicle_obstacle_detected(
                vehicle_list, max(
                    self._behavior.min_proximity_threshold, self._speed_limit / 2), up_angle_th=180, lane_offset=1)[0]
        else:
            vehicle_state, vehicle, distance = self._vehicle_obstacle_detected(
                vehicle_list, max(
                    self._behavior.min_proximity_threshold, self._speed_limit / 3), up_angle_th=30)[0]

            # Check for tailgating
            print("VEHICLE STATE IN COLLISION FUNCTION:", vehicle_state)
            if not vehicle_state and self._direction == RoadOption.LANEFOLLOW \
                    and not waypoint.is_junction and self._speed > 10 \
                    and self._behavior.tailgate_counter == 0:
                print("CHECK FOR TALIGATING")
                self._tailgating(waypoint, vehicle_list)

        return vehicle_state, vehicle, distance

    def pedestrian_avoid_manager(self, waypoint):
        """
        This module is in charge of warning in case of a collision
        with any pedestrian.

            :param location: current location of the agent
            :param waypoint: current waypoint of the agent
            :return vehicle_state: True if there is a walker nearby, False if not
            :return vehicle: nearby walker
            :return distance: distance to nearby walker
        """

        walker_list = self._world.get_actors().filter("*walker.pedestrian*")

        def dist(w):
            return w.get_location().distance(waypoint.transform.location)

        walker_list = [w for w in walker_list if dist(w) < 10]

        if self._direction == RoadOption.CHANGELANELEFT:
            walker_state, walker, distance = self._vehicle_obstacle_detected(walker_list, max(
                self._behavior.min_proximity_threshold, self._speed_limit / 2), up_angle_th=90, lane_offset=-1)[0]
        elif self._direction == RoadOption.CHANGELANERIGHT:
            walker_state, walker, distance = self._vehicle_obstacle_detected(walker_list, max(
                self._behavior.min_proximity_threshold, self._speed_limit / 2), up_angle_th=90, lane_offset=1)[0]
        else:
            walker_state, walker, distance = self._vehicle_obstacle_detected(walker_list, max(
                self._behavior.min_proximity_threshold, self._speed_limit / 3), up_angle_th=60)[0]

        return walker_state, walker, distance

    ########## DA FINIRE ##############

    def static_obstacle_avoid_manager(self, waypoint):

        obstacle_list = self._world.get_actors().filter("*static.prop*")

        def dist(v):
            return v.get_location().distance(waypoint.transform.location)

        temp_obstacle_list = [v for v in obstacle_list if dist(v) < 30]

        ego_transform = self._vehicle.get_transform()

        # Get the transform of the front of the ego
        ego_forward_vector = ego_transform.get_forward_vector()
        ego_extent = self._vehicle.bounding_box.extent.x
        ego_front_transform = ego_transform
        ego_front_transform.location += carla.Location(
            x=ego_extent * ego_forward_vector.x,
            y=ego_extent * ego_forward_vector.y,
        )

        obstacle_list = []

        for obstacle in temp_obstacle_list:
            obstacle_transform = obstacle.get_transform()
            obstacle_wpt = self._map.get_waypoint(obstacle_transform.location, lane_type=carla.LaneType.Any)

            if obstacle_wpt.road_id == waypoint.road_id and obstacle_wpt.lane_id == waypoint.lane_id and is_within_distance(
                    obstacle_transform, ego_front_transform, max_distance=50, angle_interval=[0, 30]):
                obstacle_list.append(
                    (True, obstacle, compute_distance(obstacle_transform.location, ego_transform.location)))

        sorted_obstacle_list = sorted(obstacle_list, key=lambda x: x[2])

        return sorted_obstacle_list

    def car_following_manager(self, vehicle, distance, debug=False):
        """
        Module in charge of car-following behaviors when there's
        someone in front of us.

            :param vehicle: car to follow
            :param distance: distance from vehicle
            :param debug: boolean for debugging
            :return control: carla.VehicleControl
        """

        vehicle_speed = get_speed(vehicle)
        delta_v = max(1, (self._speed - vehicle_speed) / 3.6)
        ttc = distance / delta_v if delta_v != 0 else distance / np.nextafter(0., 1.)

        # Under safety time distance, slow down.
        if self._behavior.safety_time > ttc > 0.0:
            print('Under safety time distance, slow down')
            target_speed = min([
                positive(vehicle_speed - self._behavior.speed_decrease),
                self._behavior.max_speed,
                self._speed_limit - self._behavior.speed_lim_dist])
            self._local_planner.set_speed(target_speed)
            control = self._local_planner.run_step(debug=debug)

        # Actual safety distance area, try to follow the speed of the vehicle in front.
        elif 2 * self._behavior.safety_time > ttc >= self._behavior.safety_time:
            print('Follow speed of the vehicle in front.')
            target_speed = min([
                max(self._min_speed, vehicle_speed),
                self._behavior.max_speed,
                self._speed_limit - self._behavior.speed_lim_dist])
            self._local_planner.set_speed(target_speed)
            control = self._local_planner.run_step(debug=debug)

        # Normal behavior.
        else:
            print('Normal behavior')
            target_speed = min([
                self._behavior.max_speed,
                self._speed_limit - self._behavior.speed_lim_dist])
            self._local_planner.set_speed(target_speed)
            control = self._local_planner.run_step(debug=debug)

        return control
    def _path_for_overtake(self,distance_for_overtaking,direction='left',two_way=False):

        wp = self._map.get_waypoint(self._vehicle.get_location())
        step_distance = self._sampling_resolution
        old_plan = self._local_planner._waypoints_queue

        plan = []
        plan.append((wp, RoadOption.LANEFOLLOW))

        next_wp = wp.next(step_distance)[0]

        if direction == 'left':
            side_wp = next_wp.get_left_lane()
            plan.append((next_wp, RoadOption.CHANGELANELEFT))
            plan.append((side_wp, RoadOption.LANEFOLLOW))
        else:
            side_wp = next_wp.get_lane_right()
            plan.append((next_wp, RoadOption.CHANGELANERIGHT))
            plan.append((side_wp, RoadOption.LANEFOLLOW))

        count = 0
        distance = 0
        while distance < distance_for_overtaking:
            if two_way:
                next_wps = plan[-1][0].previous(step_distance)
            else:
                next_wps = plan[-1][0].next(step_distance)
            next_wp = next_wps[0]

            distance += next_wp.transform.location.distance(plan[-1][0].transform.location)
            plan.append((next_wp, RoadOption.LANEFOLLOW))
            count = count + 1

        if two_way:
            next_wp = plan[-1][0].previous(10)[0]
            side_wp = next_wp.get_left_lane()
            plan.append((side_wp, RoadOption.CHANGELANERIGHT))
        else:
            next_wp = plan[-1][0].next(10)[0]
            side_wp = next_wp.get_left_lane()
            # plan.append((next_wp, RoadOption.LANEFOLLOW))
            plan.append((side_wp, RoadOption.CHANGELANERIGHT))

        old_plan_wp = list(map(lambda x: x[0], old_plan))
        for i in range(self._global_planner._find_closest_in_list(plan[-1][0], old_plan_wp), len(old_plan_wp)):
            plan.append(self._local_planner._waypoints_queue[i])

        self.set_global_plan(plan)

    def _check_for_vehicle(self,waypoint,distance):
        danger_vehicle_list= self._world.get_actors().filter("*vehicle*")
        def dist(v): return v.get_location().distance(waypoint.transform.location)
        left_lane_wp=waypoint.get_left_lane()
        left_lane_id= left_lane_wp.id

        danger_state=False
        danger_distance=distance
        def_danger_vehicle=False

        for danger_vehicle in danger_vehicle_list:
            danger_vehicle=danger_vehicle.transform()
            danger_wpt = self._map.get_waypoint(danger_vehicle.location, lane_type=carla.LaneType.Any)

            if danger_wpt.road_id == waypoint.road_id and danger_wpt.lane_id == waypoint.lane_id:
                d=dist(danger_vehicle)
                if is_within_distance(danger_vehicle, waypoint.transform, danger_distance, [0, 90]):
                    danger_distance = d
                    danger_state = True
                    def_danger_vehicle = danger_vehicle

            return (danger_state, def_danger_vehicle, danger_distance)




    def overtaking(self,waypoint, target, target_length, target_distance, target_speed=0, debug=False, security_distance = 3):
        danger_state,def_danger_vehicle,danger_distance=self._check_for_vehicle(waypoint,100)
        s=target_distance+target_length
        speed=min([self._behavior.max_speed,self._speed_limit-self._behavior.speed_lim_dist])/3.6
        t= s/ (speed- target_speed)
        if not danger_state:
            if danger_distance < self._behavior.braking_distance:
                self._path_for_overtake(s - 1.5, 'left', True)
                self._local_planner.set_speed(speed * 3.6)
                control = self._local_planner.run_step(debug=debug)
            else:
                control = self._local_planner.run_step(debug=debug)
        else:
            danger_vehicle_speed = get_speed(def_danger_vehicle) / 3.6
            s1 = danger_distance - danger_vehicle_speed * (t + 3)

            if s1 > s + 5:
                if target_distance < self._behavior.braking_distance + security_distance:
                    self._path_for_overtake(s - 1.5, 'left', True)
                    self._local_planner.set_speed(speed * 3.6)

                    control = self._local_planner.run_step(debug=debug)
                else:
                    control = self._local_planner.run_step(debug=debug)

            else:
                if target_distance < self._behavior.braking_distance + security_distance:
                    return self.emergency_stop()

                control = self.car_following_manager(target, target_distance)

        return control








    def run_step(self, debug=False):
        """
        Execute one step of navigation.

            :param debug: boolean for debugging
            :return control: carla.VehicleControl
        """
        self._update_information()




        control = None
        if self._behavior.tailgate_counter > 0:
            self._behavior.tailgate_counter -= 1

        ego_vehicle_loc = self._vehicle.get_location()
        ego_vehicle_wp = self._map.get_waypoint(ego_vehicle_loc)
        self._previous_wp = ego_vehicle_wp
        self._next_wp = ego_vehicle_wp.next(3)[0]
        obstacle_list = self.static_obstacle_avoid_manager(ego_vehicle_wp)
        obstacle_state = obstacle_list[0][0] if len(obstacle_list) > 0 else False

        # 1: Red lights and stops behavior
        if self.traffic_light_manager():
            return self.emergency_stop()

        # 2.1: Pedestrian avoidance behaviors
        walker_state, walker, w_distance = self.pedestrian_avoid_manager(ego_vehicle_wp)

        if walker_state:
            # Distance is computed from the center of the two cars,
            # we use bounding boxes to calculate the actual distance
            distance = w_distance - max(
                walker.bounding_box.extent.y, walker.bounding_box.extent.x) - max(
                self._vehicle.bounding_box.extent.y, self._vehicle.bounding_box.extent.x)

            # Emergency brake if the car is very close.
            if distance < self._behavior.braking_distance:
                return self.emergency_stop()

        # 2.2: Car following behaviors
        vehicle_state, vehicle, distance = self.collision_and_car_avoid_manager(ego_vehicle_wp)

        print("stato veicolo: ", vehicle_state, vehicle, distance)
        if vehicle_state:
            # Distance is computed from the center of the two cars,
            # we use bounding boxes to calculate the actual distance
            distance = distance - max(
                vehicle.bounding_box.extent.y, vehicle.bounding_box.extent.x) - max(
                self._vehicle.bounding_box.extent.y, self._vehicle.bounding_box.extent.x)
            print("distance ", distance)
            # Emergency brake if the car is very close.
            if distance < self._behavior.braking_distance:
                return self.emergency_stop()
            else:
                control = self.car_following_manager(vehicle, distance)

        # 3: Intersection behavior
        elif self._incoming_waypoint.is_junction and (self._incoming_direction in [RoadOption.LEFT, RoadOption.RIGHT]):
            target_speed = min([
                self._behavior.max_speed,
                self._speed_limit - 5])
            self._local_planner.set_speed(target_speed)
            control = self._local_planner.run_step(debug=debug)

        # static obstacle
        elif obstacle_state:

            if not 'dirtdebris' in obstacle_list[0][1].type_id:
                # Check if left lane is drivable before starting the overtaking

                ob_distance = obstacle_list[0][2]
                # print(obstacle_list [0][1].type_id)

                if len(obstacle_list) == 1:
                    ob = obstacle_list[0]
                    obstacle_length = max(ob[1].bounding_box.extent.x, ob[1].bounding_box.extent.y) * 2
                else:
                    obstacle_length = obstacle_list[-1][2] - obstacle_list[0][2]

                control = self.overtake(ego_vehicle_wp, obstacle_list[0][1], obstacle_length, ob_distance)
            else:
                if 'dirtdebris' in obstacle_list[0][1].type_id:
                    self._local_planner.set_speed(
                        min([30, self._speed_limit - self._behavior.speed_lim_dist, self._behavior.max_speed]))
                control = self._local_planner.run_step(debug=debug)

        # 4: Normal behavior
        else:
            target_speed = min([
                self._behavior.max_speed,
                self._speed_limit - self._behavior.speed_lim_dist])
            self._local_planner.set_speed(target_speed)
            control = self._local_planner.run_step(debug=debug)





        return control

    def emergency_stop(self):
        """
        Overwrites the throttle a brake values of a control to perform an emergency stop.
        The steering is kept the same to avoid going out of the lane when stopping during turns

            :param speed (carl.VehicleControl): control to be modified
        """
        print("EMERGENCY STOP!!!!!!!!!!")
        control = carla.VehicleControl()
        control.throttle = 0.0
        control.brake = self._max_brake
        control.hand_brake = False
        return control
