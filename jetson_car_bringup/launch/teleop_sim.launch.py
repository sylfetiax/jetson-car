import os
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_bringup = get_package_share_directory('jetson_car_bringup')

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_bringup, 'launch', 'sim.launch.py')
            ),
        ),
        Node(
            package='jetson_car_control',
            executable='teleop',
            output='screen',
            parameters=[{'use_sim_time': True}],
            prefix='xterm -e',    # separate terminal for keyboard input
        ),
    ])