import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image


class FakeDepthPublisher(Node):
    """Publish zero-filled 16UC1 depth images for RTAB-Map mono VO."""

    def __init__(self):
        super().__init__('fake_depth_publisher')
        self._pub = self.create_publisher(Image, 'depth', 10)
        self._sub = self.create_subscription(Image, 'image', self._callback, 10)

    def _callback(self, msg: Image):
        depth = Image()
        depth.header = msg.header
        depth.height = msg.height
        depth.width = msg.width
        depth.encoding = '16UC1'
        depth.is_bigendian = 0
        depth.step = msg.width * 2
        depth.data = bytes(msg.width * msg.height * 2)
        self._pub.publish(depth)


def main(args=None):
    rclpy.init(args=args)
    node = FakeDepthPublisher()
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
