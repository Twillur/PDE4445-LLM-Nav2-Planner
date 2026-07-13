#!/usr/bin/env python3
"""Bring up the warehouse simulation for the NL->Nav2 executor.

Launches, in the shared 0..20 m map frame:
  * Gazebo with worlds/warehouse.world (walls + four shelf rows),
  * a TurtleBot3 spawned at the charging dock (1, 1),
  * the full Nav2 stack localised on maps/warehouse.yaml.

Once this is active, feed it a plan with:
    ros2 run nl_nav2_executor execute_plan --plan plan.json

Set gui:=false to run Gazebo headless (useful for batch/CI execution).
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


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
    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(nav2, "launch", "bringup_launch.py")),
        launch_arguments={
            "map": map_yaml,
            "use_sim_time": use_sim_time,
            "params_file": params_file,
            "autostart": "true",
        }.items(),
    )

    ld = LaunchDescription()
    for arg, default in (("use_sim_time", "true"), ("gui", "true"),
                         ("x_pose", "1.0"), ("y_pose", "1.0")):
        ld.add_action(DeclareLaunchArgument(arg, default_value=default))
    ld.add_action(gzserver)
    ld.add_action(gzclient)
    ld.add_action(robot_state_publisher)
    ld.add_action(spawn)
    ld.add_action(nav2_bringup)
    return ld
