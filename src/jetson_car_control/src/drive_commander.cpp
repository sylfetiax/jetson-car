#include <chrono>
#include <memory>

#include "geometry_msgs/msg/twist_stamped.hpp"
#include "rclcpp/rclcpp.hpp"

using namespace std::chrono_literals;

class DriveCommander : public rclcpp::Node
{
public:
  DriveCommander() : Node("drive_commander")
  {
    declare_parameter<double>("linear_x", 0.3);
    declare_parameter<double>("angular_z", 0.0);
    declare_parameter<double>("publish_rate", 10.0);

    linear_x_ = get_parameter("linear_x").as_double();
    angular_z_ = get_parameter("angular_z").as_double();
    const double rate = get_parameter("publish_rate").as_double();

    pub_ = create_publisher<geometry_msgs::msg::TwistStamped>(
      "/ackermann_steering_controller/reference", 10);

    const auto period = std::chrono::duration<double>(1.0 / rate);
    timer_ = create_timer(
      std::chrono::duration_cast<std::chrono::nanoseconds>(period),
      [this]() {
        geometry_msgs::msg::TwistStamped cmd;
        cmd.header.stamp = now();
        cmd.twist.linear.x = linear_x_;
        cmd.twist.angular.z = angular_z_;
        pub_->publish(cmd);
      });

    RCLCPP_INFO(get_logger(), "Publishing linear=%.2f angular=%.2f at %.1f Hz",
      linear_x_, angular_z_, rate);
  }

private:
  rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr pub_;
  rclcpp::TimerBase::SharedPtr timer_;
  double linear_x_;
  double angular_z_;
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<DriveCommander>());
  rclcpp::shutdown();
  return 0;
}
