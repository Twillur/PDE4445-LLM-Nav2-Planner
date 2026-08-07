"""Launch the PDE4445 warehouse world with a TurtleBot3 waffle at the charging dock.

Usage:
    ros2 launch /home/william/warehouse/warehouse.launch.py

World frame convention matches map/warehouse_map.json: origin at the SW corner,
+y north, +x east. The robot spawns at the charging dock (1, 1).
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

WORLD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "warehouse.world")
SPAWN_X, SPAWN_Y = "1.0", "1.0"


def generate_launch_description():
    gazebo_launch = os.path.join(get_package_share_directory("gazebo_ros"), "launch")
    tb3_launch = os.path.join(get_package_share_directory("turtlebot3_gazebo"), "launch")

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(gazebo_launch, "gazebo.launch.py")),
            launch_arguments={"world": WORLD}.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(tb3_launch, "robot_state_publisher.launch.py")),
            launch_arguments={"use_sim_time": "true"}.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(tb3_launch, "spawn_turtlebot3.launch.py")),
            launch_arguments={"x_pose": SPAWN_X, "y_pose": SPAWN_Y}.items(),
        ),
    ])
