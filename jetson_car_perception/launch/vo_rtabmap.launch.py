from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    publish_tf = LaunchConfiguration('publish_tf')

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='true',
            description='Use simulation clock from /clock',
        ),
        DeclareLaunchArgument(
            'publish_tf',
            default_value='true',
            description='VO publishes odom→base_link TF',
        ),

        Node(
            package='jetson_car_perception',
            executable='mono_vo',
            name='mono_vo',
            parameters=[{
                'use_sim_time': use_sim_time,
                'frame_id': 'base_link',
                'odom_frame_id': 'odom',
                'publish_tf': publish_tf,
            }],
            remappings=[
                ('image', '/camera/image_raw'),
                ('camera_info', '/camera/camera_info'),
                ('odom', '/vo/odom'),
            ],
        ),
    ])
