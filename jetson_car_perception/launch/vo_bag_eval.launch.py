import os
from datetime import datetime

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    LogInfo,
    RegisterEventHandler,
    TimerAction,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg = get_package_share_directory('jetson_car_perception')
    bags_dir = os.path.expanduser('~/mldl/jetson/ros2/car_ws/bags')
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    default_bag = os.path.join(bags_dir, 'driving_figure8_vo_track_01')
    default_record = os.path.join(bags_dir, f'vo_output_{stamp}')

    bag = LaunchConfiguration('bag')
    record = LaunchConfiguration('record')
    record_output = LaunchConfiguration('record_output')
    rate = LaunchConfiguration('rate')
    rviz = LaunchConfiguration('rviz')

    sim = {'use_sim_time': True}

    bag_play = ExecuteProcess(
        cmd=['ros2', 'bag', 'play', bag, '--clock', '--rate', rate],
        output='screen',
        name='bag_play',
    )

    vo = Node(
        package='jetson_car_perception',
        executable='mono_vo',
        name='mono_vo',
        parameters=[{
            **sim,
            'frame_id': 'base_link',
            'odom_frame_id': 'odom',
            'publish_tf': False,
            'align_gt_origin': True,
        }],
        remappings=[
            ('image', '/camera/image_raw'),
            ('camera_info', '/camera/camera_info'),
            ('odom', '/vo/odom'),
        ],
    )

    tf_relay = Node(
        package='jetson_car_perception',
        executable='tf_relay',
        name='tf_relay',
        parameters=[sim],
    )

    gt_path = Node(
        package='jetson_car_perception',
        executable='odom_to_path',
        name='gt_path',
        parameters=[{
            **sim,
            'odom_topic': '/ackermann_steering_controller/odometry',
            'path_topic': '/gt/path',
        }],
    )

    vo_path = Node(
        package='jetson_car_perception',
        executable='odom_to_path',
        name='vo_path',
        parameters=[{
            **sim,
            'odom_topic': '/vo/odom',
            'path_topic': '/vo/path',
        }],
    )

    bag_record = ExecuteProcess(
        cmd=[
            'ros2', 'bag', 'record',
            '--use-sim-time',
            '--topics', '/vo/odom',
            '-o', record_output,
        ],
        output='screen',
        name='bag_record',
        condition=IfCondition(record),
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', os.path.join(pkg, 'config', 'vo_eval.rviz')],
        parameters=[sim],
        condition=IfCondition(rviz),
    )

    start_pipeline = TimerAction(
        period=2.0,
        actions=[
            vo,
            tf_relay,
            gt_path,
            vo_path,
            bag_record,
            LogInfo(msg=['Mono VO started. Green=GT, orange=VO.']),
        ],
    )

    start_rviz = TimerAction(
        period=4.0,
        actions=[
            rviz_node,
            LogInfo(msg=['RViz started.']),
        ],
    )

    on_bag_done = RegisterEventHandler(
        OnProcessExit(
            target_action=bag_play,
            on_exit=[
                LogInfo(msg=[
                    'Bag finished. Inspect trajectories in RViz, then Ctrl+C. '
                    'VO bag (if recording): ', record_output,
                ]),
            ],
        )
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'bag', default_value=default_bag,
            description='Input rosbag to replay'),
        DeclareLaunchArgument(
            'record', default_value='true',
            description='Record /vo/odom to a new rosbag'),
        DeclareLaunchArgument(
            'record_output', default_value=default_record,
            description='Output directory for VO bag (must not already exist)'),
        DeclareLaunchArgument(
            'rate', default_value='1.0',
            description='Bag playback rate'),
        DeclareLaunchArgument(
            'rviz', default_value='true',
            description='Open RViz trajectory comparison'),

        LogInfo(msg=['Playing bag: ', bag]),
        bag_play,
        start_pipeline,
        start_rviz,
        on_bag_done,
    ])
