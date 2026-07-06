import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    pkg_bringup = get_package_share_directory('jetson_car_bringup')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    world = os.path.join(pkg_bringup, 'worlds', 'empty.sdf')    # shipped with bringup (not in ros_gz_sim on Jazzy)

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),    # for downstream includes
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
            ),
            launch_arguments={
                'gz_args': f'-r {world}',    # -r = run sim with GUI
            }.items(),
        ),
    ])
