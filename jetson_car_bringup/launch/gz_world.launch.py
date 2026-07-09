import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_bringup = get_package_share_directory('jetson_car_bringup')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    default_world = os.path.join(pkg_bringup, 'worlds', 'vo_track.sdf')

    world = LaunchConfiguration('world')

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument(
            'world',
            default_value=default_world,
            description='Full path to Gazebo world SDF (vo_track.sdf for VO, empty.sdf for control-only)',
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
            ),
            launch_arguments={
                'gz_args': ['-r ', world],
            }.items(),
        ),
    ])
