#!/usr/bin/env python3
"""Bring up the warehouse simulation for the NL->Nav2 executor.

Launches, in the shared 0..20 m map frame:
  * Gazebo with worlds/warehouse.world (walls + four shelf rows),
  * a TurtleBot3 spawned at the charging dock (1, 1),
  * the Nav2 navigation stack over maps/warehouse.yaml.

Localisation modes (localization:=...):
  * ground_truth (default) - the Gazebo odom frame coincides with the map
    origin (both at the world's SW corner), so map->odom is a static identity
    transform and Nav2 uses Gazebo's ground-truth odometry. Robust and exact;
    appropriate for a sim demo where localisation is not the contribution.
  * amcl - the full AMCL localisation stack (bringup_launch) for when a real
    SLAM map replaces the mock.

Once active, feed it a plan with:
    ros2 run nl_nav2_executor execute_plan --plan plan.json

Set gui:=false to run Gazebo headless.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition, LaunchConfigurationEquals
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory("nl_nav2_executor")
    tb3 = get_package_share_directory("turtlebot3_gazebo")
    gazebo_ros = get_package_share_directory("gazebo_ros")
    nav2 = get_package_share_directory("nav2_bringup")

    use_sim_time = LaunchConfiguration("use_sim_time", default="true")
    gui = LaunchConfiguration("gui", default="true")
    x_pose = LaunchConfiguration("x_pose", default="1.0")   # charging_dock
    y_pose = LaunchConfiguration("y_pose", default="1.0")

    world = os.path.join(pkg, "worlds", "warehouse.world")
    map_yaml = os.path.join(pkg, "maps", "warehouse.yaml")
    params_file = os.path.join(pkg, "params", "nav2_params.yaml")

    ground_truth = LaunchConfigurationEquals("localization", "ground_truth")
    amcl = LaunchConfigurationEquals("localization", "amcl")

    # --- Gazebo + robot ------------------------------------------------------
    gzserver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(gazebo_ros, "launch", "gzserver.launch.py")),
        launch_arguments={"world": world}.items(),
    )
    gzclient = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(gazebo_ros, "launch", "gzclient.launch.py")),
        condition=IfCondition(gui),
    )
    robot_state_publisher = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(tb3, "launch", "robot_state_publisher.launch.py")),
        launch_arguments={"use_sim_time": use_sim_time}.items(),
    )
    spawn = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(tb3, "launch", "spawn_turtlebot3.launch.py")),
        launch_arguments={"x_pose": x_pose, "y_pose": y_pose,
                          "use_sim_time": use_sim_time}.items(),
    )

    # --- ground_truth localisation: map_server + static map->odom + nav stack -
    map_server = Node(
        package="nav2_map_server", executable="map_server", name="map_server",
        output="screen", parameters=[{"use_sim_time": True, "yaml_filename": map_yaml}],
        condition=ground_truth,
    )
    map_lifecycle = Node(
        package="nav2_lifecycle_manager", executable="lifecycle_manager",
        name="lifecycle_manager_localization", output="screen",
        parameters=[{"use_sim_time": True, "autostart": True, "node_names": ["map_server"]}],
        condition=ground_truth,
    )
    map_to_odom = Node(
        package="tf2_ros", executable="static_transform_publisher", name="map_to_odom",
        arguments=["--frame-id", "map", "--child-frame-id", "odom"],
        parameters=[{"use_sim_time": True}], condition=ground_truth,
    )
    # One container hosting the whole nav stack: far fewer processes than the
    # default (un-composed) launch, so the bt<->controller action handshakes
    # don't time out under the loopback-pinned CycloneDDS config.
    nav2_container = Node(
        package="rclcpp_components", executable="component_container_isolated",
        name="nav2_container", output="screen",
        parameters=[params_file, {"use_sim_time": True}],
        condition=ground_truth,
    )
    navigation = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(nav2, "launch", "navigation_launch.py")),
        launch_arguments={"use_sim_time": use_sim_time, "params_file": params_file,
                          "autostart": "true", "use_composition": "True",
                          "container_name": "nav2_container"}.items(),
        condition=ground_truth,
    )

    # --- amcl localisation: the full bringup ---------------------------------
    full_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(nav2, "launch", "bringup_launch.py")),
        launch_arguments={"map": map_yaml, "use_sim_time": use_sim_time,
                          "params_file": params_file, "autostart": "true"}.items(),
        condition=amcl,
    )

    ld = LaunchDescription()
    for arg, default in (("use_sim_time", "true"), ("gui", "true"),
                         ("x_pose", "1.0"), ("y_pose", "1.0"),
                         ("localization", "ground_truth")):
        ld.add_action(DeclareLaunchArgument(arg, default_value=default))
    for action in (gzserver, gzclient, robot_state_publisher, spawn,
                   map_server, map_lifecycle, map_to_odom, nav2_container,
                   navigation, full_bringup):
        ld.add_action(action)
    return ld
