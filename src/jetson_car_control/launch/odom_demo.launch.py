from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    odom_node = Node(
        package='jetson_car_control',
        executable='fake_odom',
        name='fake_odom',
        namespace='',
        output='screen',
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', '/home/maksym/mldl/jetson/ros2/car_ws/src/jetson_car_control/rviz/odom_test.rviz']
    )

    return LaunchDescription([
        odom_node,
        rviz_node
    ])