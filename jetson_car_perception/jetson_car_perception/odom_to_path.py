import math

import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry, Path
from geometry_msgs.msg import PoseStamped


def _valid_pose(msg: Odometry) -> bool:
    p = msg.pose.pose.position
    q = msg.pose.pose.orientation
    if math.isnan(p.x) or math.isnan(p.y) or math.isnan(p.z):
        return False
    norm = math.sqrt(q.x * q.x + q.y * q.y + q.z * q.z + q.w * q.w)
    return norm > 1e-3


class OdomToPath(Node):
    def __init__(self):
        super().__init__('odom_to_path')
        self.declare_parameter('odom_topic', 'odom')
        self.declare_parameter('path_topic', 'path')
        self.declare_parameter('max_poses', 10000)
        self._max_poses = self.get_parameter('max_poses').value
        odom_topic = self.get_parameter('odom_topic').value
        path_topic = self.get_parameter('path_topic').value

        self._path = Path()
        self._pub = self.create_publisher(Path, path_topic, 10)
        self._sub = self.create_subscription(
            Odometry, odom_topic, self._callback, 10)
        self.get_logger().info(
            f'Converting {odom_topic} -> {path_topic}')

    def _callback(self, msg: Odometry):
        if not _valid_pose(msg):
            return
        pose = PoseStamped()
        pose.header = msg.header
        pose.pose = msg.pose.pose
        self._path.header = msg.header
        self._path.poses.append(pose)
        if len(self._path.poses) > self._max_poses:
            self._path.poses.pop(0)
        self._pub.publish(self._path)


def main(args=None):
    rclpy.init(args=args)
    node = OdomToPath()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
