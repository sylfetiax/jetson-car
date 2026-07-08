import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory
from controller_manager.launch_utils import generate_controllers_spawner_launch_description


def generate_launch_description():
    pkg_desc = get_package_share_directory('jetson_car_description')
    pkg_bringup = get_package_share_directory('jetson_car_bringup')
    xacro_file = os.path.join(pkg_desc, 'urdf', 'jetson_car.urdf.xacro')
    controllers_file = os.path.join(pkg_desc, 'config', 'controllers.yaml')
    robot_description = ParameterValue(
        Command(['xacro ', xacro_file]),
        value_type=str,
    )    # URDF XML must be passed as a string, not parsed as YAML
    use_sim_time = LaunchConfiguration('use_sim_time')
    x = LaunchConfiguration('x')
    y = LaunchConfiguration('y')
    z = LaunchConfiguration('z')
    yaw = LaunchConfiguration('yaw')

    spawner_launch = generate_controllers_spawner_launch_description(
        ['joint_state_broadcaster', 'ackermann_steering_controller'],
        controller_params_files=[controllers_file],
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('x', default_value='0'),
        DeclareLaunchArgument('y', default_value='0'),
        DeclareLaunchArgument('z', default_value='0.1'),
        DeclareLaunchArgument('yaw', default_value='0'),

        IncludeLaunchDescription(    # starts gz sim + empty world
            PythonLaunchDescriptionSource(
                os.path.join(pkg_bringup, 'launch', 'gz_world.launch.py')
            ),
        ),

        Node(    # publishes /tf and latched /robot_description
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{
                'robot_description': robot_description,
                'use_sim_time': use_sim_time,
            }],
        ),

        Node(    # bridges Gazebo sim clock → ROS /clock (must NOT use sim time)
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
            output='screen',
        ),

        Node(    # inserts robot from /robot_description topic into Gazebo world
            package='ros_gz_sim',
            executable='create',
            arguments=[
                '-name', 'jetson_car',
                '-topic', 'robot_description',
                '-x', x, '-y', y, '-z', z, '-Y', yaw,
            ],
            output='screen',
        ),
    ] + list(spawner_launch.entities))
