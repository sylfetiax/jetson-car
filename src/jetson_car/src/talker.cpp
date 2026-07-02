#include <chrono>
#include <memory>
#include <string>


#include "rclcpp/rclcpp.hpp"
#include "std_msgs/msg/string.hpp"

using namespace std::chrono_literals;

class Talker : public rclcpp::Node {
public:
  Talker() : Node("talker") {
    declare_parameter<double>("publish_rate", 1.0);
    double rate = get_parameter("publish_rate").as_double();

    publisher_ = create_publisher<std_msgs::msg::String>("chatter", 10);

    auto period = std::chrono::duration<double>(1.0 / rate);
    timer_ = create_wall_timer(
      std::chrono::duration_cast<std::chrono::milliseconds>(period),
      [this]() {
        auto msg = std_msgs::msg::String();
        msg.data = "Hello, count: " + std::to_string(count_++);
        publisher_->publish(msg);
        RCLCPP_INFO(get_logger(), "Publishing: '%s'", msg.data.c_str());
      });
  }

private:
  rclcpp::Publisher<std_msgs::msg::String>::SharedPtr publisher_;
  rclcpp::TimerBase::SharedPtr timer_;
  size_t count_{0};
};

int main(int argc, char * argv[]) {
  rclcpp::init(argc, argv);
  auto node = std::make_shared<Talker>();
  rclcpp::spin(node);
  rclcpp::shutdown();
  return 0;
}
