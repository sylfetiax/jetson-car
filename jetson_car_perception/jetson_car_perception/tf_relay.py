import rclpy
from rclpy.node import Node
from tf2_msgs.msg import TFMessage


class TfRelay(Node):
    """Republish controller tf_odometry onto /tf for RViz and VO."""

    def __init__(self):
        super().__init__('tf_relay')
        self.declare_parameter(
            'input_topic', '/ackermann_steering_controller/tf_odometry')
        input_topic = self.get_parameter('input_topic').value
        self._pub = self.create_publisher(TFMessage, '/tf', 10)
        self._sub = self.create_subscription(
            TFMessage, input_topic, self._callback, 10)
        self.get_logger().info(f'Relaying {input_topic} -> /tf')

    def _callback(self, msg: TFMessage):
        self._pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = TfRelay()
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
