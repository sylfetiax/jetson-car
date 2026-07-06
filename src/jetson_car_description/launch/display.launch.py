import os


from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import Command
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    pkg = get_package_share_directory('jetson_car_description')    # installed share path
    xacro_file = os.path.join(pkg, 'urdf', 'jetson_car.urdf.xacro')
    rviz_config = os.path.join(pkg, 'config', 'display.rviz')

    robot_description = ParameterValue(
        Command(['xacro ', xacro_file, ' lock_drive_joints:=true']),
        value_type=str,
    )    # lock roll joints for steer-only GUI testing

    return LaunchDescription([
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{'robot_description': robot_description}],    # feeds /robot_description + /tf
            output='screen',
        ),
        Node(
            package='joint_state_publisher_gui',
            executable='joint_state_publisher_gui',    # publishes /joint_states from sliders
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_config],    # load saved display config
        ),
    ])