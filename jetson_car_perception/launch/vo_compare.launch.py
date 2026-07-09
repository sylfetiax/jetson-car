import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory('jetson_car_perception')
    use_sim_time = LaunchConfiguration('use_sim_time')
    publish_tf = LaunchConfiguration('publish_tf')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time', default_value='true',
            description='Use simulation clock from /clock'),
        DeclareLaunchArgument(
            'publish_tf', default_value='true',
            description='VO publishes odom→base_link TF'),

        Node(
            package='jetson_car_perception',
            executable='mono_vo',
            name='mono_vo',
            parameters=[{
                'use_sim_time': use_sim_time,
                'frame_id': 'base_link',
                'odom_frame_id': 'odom',
                'publish_tf': publish_tf,
                'align_gt_origin': True,
            }],
            remappings=[
                ('image', '/camera/image_raw'),
                ('camera_info', '/camera/camera_info'),
                ('odom', '/vo/odom'),
            ],
        ),

        Node(
            package='jetson_car_perception',
            executable='odom_to_path',
            name='gt_path',
            parameters=[{
                'use_sim_time': use_sim_time,
                'odom_topic': '/ackermann_steering_controller/odometry',
                'path_topic': '/gt/path',
            }],
        ),

        Node(
            package='jetson_car_perception',
            executable='odom_to_path',
            name='vo_path',
            parameters=[{
                'use_sim_time': use_sim_time,
                'odom_topic': '/vo/odom',
                'path_topic': '/vo/path',
            }],
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', os.path.join(pkg, 'config', 'vo_eval.rviz')],
            parameters=[{'use_sim_time': use_sim_time}],
        ),
    ])
