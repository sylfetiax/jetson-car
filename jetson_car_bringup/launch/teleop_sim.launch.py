import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_bringup = get_package_share_directory('jetson_car_bringup')
    default_world = os.path.join(pkg_bringup, 'worlds', 'vo_track.sdf')

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=default_world,
            description='Gazebo world SDF (default vo_track.sdf)',
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_bringup, 'launch', 'sim.launch.py')
            ),
            launch_arguments={'world': LaunchConfiguration('world')}.items(),
        ),
        Node(
            package='jetson_car_control',
            executable='teleop',
            output='screen',
            parameters=[{'use_sim_time': True}],
            prefix='xterm -e',
        ),
    ])
