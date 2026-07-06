#include <cmath> // std::cos, std::sin, M_PI_2 for circular motion math
#include <memory> // std::make_shared, std::shared_ptr
#include <string> // std::string for frame name parameters


#include "geometry_msgs/msg/transform_stamped.hpp" // TransformStamped message for tf broadcast
#include "nav_msgs/msg/odometry.hpp" // Odometry message published on /odom
#include "rclcpp/rclcpp.hpp" // Node, Publisher, Timer, parameters
#include "tf2/LinearMath/Quaternion.h" // tf2::Quaternion for yaw-to-quaternion conversion
#include "tf2_ros/static_transform_broadcaster.h" // StaticTransformBroadcaster for sensor mounts
#include "tf2_ros/transform_broadcaster.h" // TransformBroadcaster for odom → base_link

class FakeOdom : public rclcpp::Node // regular Node (not lifecycle) for simplicity
{
public:
  FakeOdom()
  : Node("fake_odom") // node name used by ros2 param and ros2 node list
  {
    declare_parameter<std::string>("odom_frame", "odom"); // parent frame (REP-103)
    declare_parameter<std::string>("base_frame", "base_link"); // child frame (REP-103)
    declare_parameter<double>("radius", 2.0); // circle radius in meters
    declare_parameter<double>("speed", 0.5); // tangential speed in m/s
    declare_parameter<double>("publish_rate", 20.0); // odometry + tf publish frequency in Hz

    odom_frame_ = get_parameter("odom_frame").as_string(); // read frame name into member
    base_frame_ = get_parameter("base_frame").as_string(); // read frame name into member
    radius_ = get_parameter("radius").as_double(); // circle radius
    speed_ = get_parameter("speed").as_double(); // movement speed
    const double rate = get_parameter("publish_rate").as_double(); // publish rate

    odom_pub_ = create_publisher<nav_msgs::msg::Odometry>("/odom", 10); // odometry topic
    tf_broadcaster_ = std::make_shared<tf2_ros::TransformBroadcaster>(this); // dynamic tf
    static_broadcaster_ = std::make_shared<tf2_ros::StaticTransformBroadcaster>(this); // static tf

    publish_static_transforms(); // send camera_link and imu_link transforms once at startup
    start_time_ = now(); // record start time for elapsed-time circular motion

    const auto period = std::chrono::duration<double>(1.0 / rate); // convert Hz to seconds
    timer_ = create_timer( // sim-time-aware timer (not wall timer)
      std::chrono::duration_cast<std::chrono::milliseconds>(period), // period in ms
      std::bind(&FakeOdom::on_timer, this)); // bind member function as callback
  }

private:
  void publish_static_transforms() // called once in constructor
  {
    geometry_msgs::msg::TransformStamped camera_tf; // transform for camera mount
    camera_tf.header.stamp = now(); // timestamp required even for static transforms
    camera_tf.header.frame_id = base_frame_; // parent: base_link
    camera_tf.child_frame_id = "camera_link"; // child: camera sensor frame
    camera_tf.transform.translation.x = 0.10; // 10 cm forward of base_link
    camera_tf.transform.translation.y = 0.0; // centered laterally
    camera_tf.transform.translation.z = 0.15; // 15 cm above base_link
    camera_tf.transform.rotation.w = 1.0; // identity rotation (no tilt)

    geometry_msgs::msg::TransformStamped imu_tf; // transform for IMU mount
    imu_tf.header.stamp = now(); // timestamp
    imu_tf.header.frame_id = base_frame_; // parent: base_link
    imu_tf.child_frame_id = "imu_link"; // child: IMU sensor frame
    imu_tf.transform.translation.x = 0.0; // IMU at base_link origin (x)
    imu_tf.transform.translation.y = 0.0; // centered (y)
    imu_tf.transform.translation.z = 0.0; // at base_link height (z)
    imu_tf.transform.rotation.w = 1.0; // identity rotation

    static_broadcaster_->sendTransform({camera_tf, imu_tf}); // publish both static transforms
  }

  void on_timer() // called every 1/rate seconds
  {
    const double t = (now() - start_time_).seconds(); // elapsed time since node started
    const double omega = speed_ / radius_; // angular velocity ω = v/r (rad/s)
    const double x = radius_ * std::cos(omega * t); // x position on circle
    const double y = radius_ * std::sin(omega * t); // y position on circle
    const double yaw = omega * t + M_PI_2; // heading tangent to circle (offset by π/2)
    const double vx = -radius_ * omega * std::sin(omega * t); // x velocity (derivative of x)
    const double vy = radius_ * omega * std::cos(omega * t); // y velocity (derivative of y)

    tf2::Quaternion q; // quaternion for orientation
    q.setRPY(0.0, 0.0, yaw); // roll=0, pitch=0, yaw=heading

    nav_msgs::msg::Odometry odom; // odometry message to fill and publish
    odom.header.stamp = now(); // current time stamp (critical for tf)
    odom.header.frame_id = odom_frame_; // parent frame: "odom"
    odom.child_frame_id = base_frame_; // child frame: "base_link"
    odom.pose.pose.position.x = x; // x position in odom frame
    odom.pose.pose.position.y = y; // y position in odom frame
    odom.pose.pose.orientation.x = q.x(); // quaternion x
    odom.pose.pose.orientation.y = q.y(); // quaternion y
    odom.pose.pose.orientation.z = q.z(); // quaternion z
    odom.pose.pose.orientation.w = q.w(); // quaternion w
    odom.twist.twist.linear.x = vx; // forward velocity in child frame (approx for circle)
    odom.twist.twist.linear.y = vy; // lateral velocity component
    odom.twist.twist.angular.z = omega; // rotation rate around z
    odom_pub_->publish(odom); // publish odometry message

    geometry_msgs::msg::TransformStamped odom_tf; // matching tf transform
    odom_tf.header = odom.header; // copy stamp and frame_id from odometry
    odom_tf.child_frame_id = base_frame_; // child: base_link
    odom_tf.transform.translation.x = x; // same position as odometry
    odom_tf.transform.translation.y = y; // same position as odometry
    odom_tf.transform.rotation = odom.pose.pose.orientation; // same orientation as odometry
    tf_broadcaster_->sendTransform(odom_tf); // broadcast odom → base_link transform
  }

  rclcpp::Publisher<nav_msgs::msg::Odometry>::SharedPtr odom_pub_; // odometry publisher
  std::shared_ptr<tf2_ros::TransformBroadcaster> tf_broadcaster_; // dynamic transform broadcaster
  std::shared_ptr<tf2_ros::StaticTransformBroadcaster> static_broadcaster_; // static broadcaster
  rclcpp::TimerBase::SharedPtr timer_; // periodic timer for odometry updates
  rclcpp::Time start_time_; // node start time for elapsed time calculation
  std::string odom_frame_; // odom frame name (from parameter)
  std::string base_frame_; // base_link frame name (from parameter)
  double radius_{2.0}; // circle radius (m)
  double speed_{0.5}; // tangential speed (m/s)
};

int main(int argc, char * argv[]) // standard node entry point
{
  rclcpp::init(argc, argv); // initialize ROS 2
  rclcpp::spin(std::make_shared<FakeOdom>()); // create node and spin (process timer callbacks)
  rclcpp::shutdown(); // cleanup
  return 0;
}
