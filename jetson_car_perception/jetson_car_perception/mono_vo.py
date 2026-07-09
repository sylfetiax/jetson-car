from __future__ import annotations

import math

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from geometry_msgs.msg import TransformStamped
from message_filters import ApproximateTimeSynchronizer, Subscriber
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import CameraInfo, Image
from tf2_ros import TransformBroadcaster


def _quat_from_yaw(yaw: float) -> tuple[float, float, float, float]:
    """Yaw-only quaternion (x, y, z, w) for planar ground robot."""
    half = 0.5 * yaw
    return 0.0, 0.0, math.sin(half), math.cos(half)


class MonoVO(Node):
    def __init__(self):
        super().__init__('mono_vo')
        self.declare_parameter('frame_id', 'base_link')
        self.declare_parameter('odom_frame_id', 'odom')
        self.declare_parameter('publish_tf', True)
        self.declare_parameter('min_matches', 25)
        self.declare_parameter('max_features', 1500)
        self.declare_parameter('scale', 0.03)
        self.declare_parameter('align_gt_origin', False)
        self.declare_parameter(
            'gt_odom_topic', '/ackermann_steering_controller/odometry')

        self._frame_id = self.get_parameter('frame_id').value
        self._odom_frame = self.get_parameter('odom_frame_id').value
        self._publish_tf = bool(self.get_parameter('publish_tf').value)
        self._min_matches = int(self.get_parameter('min_matches').value)
        self._scale = float(self.get_parameter('scale').value)
        align_gt = bool(self.get_parameter('align_gt_origin').value)
        gt_topic = self.get_parameter('gt_odom_topic').value
        max_features = int(self.get_parameter('max_features').value)

        self._bridge = CvBridge()
        self._orb = cv2.ORB_create(nfeatures=max_features)
        self._bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

        self._K: np.ndarray | None = None
        self._prev_kp = None
        self._prev_des = None

        # Planar pose in odom (x, y, yaw)
        self._x = 0.0
        self._y = 0.0
        self._yaw = 0.0
        self._frames = 0
        self._good = 0

        # Optional GT origin alignment
        self._offset_x = 0.0
        self._offset_y = 0.0
        self._offset_yaw = 0.0
        self._gt_aligned = not align_gt

        self._R_bo = np.array([
            [0.0, 0.0, 1.0],
            [-1.0, 0.0, 0.0],
            [0.0, -1.0, 0.0],
        ], dtype=np.float64)

        self._odom_pub = self.create_publisher(Odometry, 'odom', 10)
        self._tf_broadcaster = (
            TransformBroadcaster(self) if self._publish_tf else None)

        if align_gt:
            self.create_subscription(
                Odometry, gt_topic, self._gt_origin_callback, 10)
            self.get_logger().info(
                f'Will align VO origin to first message on {gt_topic}')

        image_sub = Subscriber(self, Image, 'image')
        info_sub = Subscriber(self, CameraInfo, 'camera_info')
        self._sync = ApproximateTimeSynchronizer(
            [image_sub, info_sub], queue_size=30, slop=0.1)
        self._sync.registerCallback(self._callback)

        self.get_logger().info(
            f'Mono VO ready (ORB+Essential, planar). '
            f'scale={self._scale} m/step publish_tf={self._publish_tf}')

    def _gt_origin_callback(self, msg: Odometry):
        if self._gt_aligned:
            return
        q = msg.pose.pose.orientation
        gt_yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z))
        self._offset_x = msg.pose.pose.position.x - self._x
        self._offset_y = msg.pose.pose.position.y - self._y
        self._offset_yaw = gt_yaw - self._yaw
        self._gt_aligned = True
        self.get_logger().info(
            f'Aligned VO origin to GT: '
            f'offset=({self._offset_x:.3f},{self._offset_y:.3f}) '
            f'yaw={self._offset_yaw:.3f}')

    def _callback(self, image_msg: Image, info_msg: CameraInfo):
        if self._K is None:
            self._K = np.array(info_msg.k, dtype=np.float64).reshape(3, 3)
            self.get_logger().info(
                f'Camera {info_msg.width}x{info_msg.height} '
                f'fx={self._K[0,0]:.1f} fy={self._K[1,1]:.1f}')

        try:
            frame = self._bridge.imgmsg_to_cv2(
                image_msg, desired_encoding='bgr8')
        except Exception as exc:  # noqa: BLE001
            self.get_logger().warn(f'cv_bridge failed: {exc}')
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        kp, des = self._orb.detectAndCompute(gray, None)
        self._frames += 1

        if des is None or len(kp) < self._min_matches:
            self._prev_kp, self._prev_des = kp, des
            self._publish(image_msg.header.stamp)
            return

        if self._prev_des is None or self._prev_kp is None:
            self._prev_kp, self._prev_des = kp, des
            self._publish(image_msg.header.stamp)
            return

        knn = self._bf.knnMatch(self._prev_des, des, k=2)
        good = []
        for pair in knn:
            if len(pair) != 2:
                continue
            m, n = pair
            if m.distance < 0.75 * n.distance:
                good.append(m)

        if len(good) < self._min_matches:
            self._prev_kp, self._prev_des = kp, des
            self._publish(image_msg.header.stamp)
            return

        pts1 = np.float32([self._prev_kp[m.queryIdx].pt for m in good])
        pts2 = np.float32([kp[m.trainIdx].pt for m in good])

        E, mask = cv2.findEssentialMat(
            pts1, pts2, self._K,
            method=cv2.RANSAC, prob=0.999, threshold=1.0)
        if E is None or mask is None:
            self._prev_kp, self._prev_des = kp, des
            self._publish(image_msg.header.stamp)
            return

        _, R, t, mask_pose = cv2.recoverPose(
            E, pts1, pts2, self._K, mask=mask)
        inliers = int(mask_pose.sum()) if mask_pose is not None else 0
        if inliers < max(10, self._min_matches // 2):
            self._prev_kp, self._prev_des = kp, des
            self._publish(image_msg.header.stamp)
            return

        t_body = self._R_bo @ t
        dx = -float(t_body[0, 0]) * self._scale
        dy = -float(t_body[1, 0]) * self._scale

        R_body = self._R_bo @ R @ self._R_bo.T
        dyaw = -math.atan2(R_body[1, 0], R_body[0, 0])

        c, s = math.cos(self._yaw), math.sin(self._yaw)
        self._x += c * dx - s * dy
        self._y += s * dx + c * dy
        self._yaw += dyaw
        self._good += 1

        if self._good % 30 == 0:
            self.get_logger().info(
                f'VO ok {self._good}/{self._frames} '
                f'inliers={inliers} '
                f'xy=({self._x:.2f},{self._y:.2f}) yaw={self._yaw:.2f}')

        self._prev_kp, self._prev_des = kp, des
        self._publish(image_msg.header.stamp)

    def _publish(self, stamp):
        x = self._x + self._offset_x
        y = self._y + self._offset_y
        yaw = self._yaw + self._offset_yaw
        qx, qy, qz, qw = _quat_from_yaw(yaw)

        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = self._odom_frame
        odom.child_frame_id = self._frame_id
        odom.pose.pose.position.x = x
        odom.pose.pose.position.y = y
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation.x = qx
        odom.pose.pose.orientation.y = qy
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw
        odom.pose.covariance[0] = 0.05
        odom.pose.covariance[7] = 0.05
        odom.pose.covariance[35] = 0.05
        self._odom_pub.publish(odom)

        if self._tf_broadcaster is not None:
            tf = TransformStamped()
            tf.header.stamp = stamp
            tf.header.frame_id = self._odom_frame
            tf.child_frame_id = self._frame_id
            tf.transform.translation.x = x
            tf.transform.translation.y = y
            tf.transform.translation.z = 0.0
            tf.transform.rotation.x = qx
            tf.transform.rotation.y = qy
            tf.transform.rotation.z = qz
            tf.transform.rotation.w = qw
            self._tf_broadcaster.sendTransform(tf)


def main(args=None):
    rclpy.init(args=args)
    node = MonoVO()
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
