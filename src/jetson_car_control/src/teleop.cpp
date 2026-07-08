#include <termios.h>
#include <unistd.h>

#include <atomic>
#include <chrono>
#include <cmath>
#include <memory>
#include <thread>

#include "geometry_msgs/msg/twist_stamped.hpp"
#include "rclcpp/rclcpp.hpp"

// ang-bang steering
class TeleopNode : public rclcpp::Node
{
public:
  TeleopNode() : Node("teleop")
  {
    declare_parameter<double>("max_linear", 0.5);
    declare_parameter<double>("max_angular", 1.0);  
    declare_parameter<double>("linear_step", 0.05);
    declare_parameter<double>("publish_rate", 20.0);
    declare_parameter<double>("timeout_sec", 1.0);

    max_linear_ = get_parameter("max_linear").as_double();
    max_angular_ = get_parameter("max_angular").as_double();
    linear_step_ = get_parameter("linear_step").as_double();
    timeout_sec_ = get_parameter("timeout_sec").as_double();

    pub_ = create_publisher<geometry_msgs::msg::TwistStamped>(
      "/ackermann_steering_controller/reference", 10);

    const double rate = get_parameter("publish_rate").as_double();
    const auto period = std::chrono::duration<double>(1.0 / rate);
    timer_ = create_timer(
      std::chrono::duration_cast<std::chrono::nanoseconds>(period),
      [this]() { publish_cmd(); });

    last_key_time_ = now();
    keyboard_thread_ = std::thread(&TeleopNode::keyboard_loop, this);
    print_instructions();
  }

  ~TeleopNode() override
  {
    running_ = false;
    if (keyboard_thread_.joinable()) {
      keyboard_thread_.join();
    }
    publish_stop();
  }

private:
  void print_instructions()
  {
    RCLCPP_INFO(get_logger(),
      "\n--- Teleop Controls (bang-bang steer) ---\n"
      "  w/s : increase/decrease forward speed\n"
      "  a   : full steer LEFT (not gradual)\n"
      "  d   : full steer RIGHT\n"
      "  c   : center wheels (straight), keep speed\n"
      "  space : stop immediately\n"
      "  q : quit\n"
      "-----------------------------------------");
  }

  static char read_key()
  {
    char ch = 0;
    if (read(STDIN_FILENO, &ch, 1) < 0) {
      return 0;
    }
    return ch;
  }

  void keyboard_loop()
  {
    struct termios oldt{};
    struct termios newt{};
    tcgetattr(STDIN_FILENO, &oldt);
    newt = oldt;
    newt.c_lflag &= ~(ICANON | ECHO);
    tcsetattr(STDIN_FILENO, TCSANOW, &newt);

    while (running_ && rclcpp::ok()) {
      const char key = read_key();
      if (key == 0) {
        continue;
      }
      last_key_time_ = now();

      switch (key) {
        case 'w':
          target_linear_ = std::min(target_linear_.load() + linear_step_, max_linear_);
          break;
        case 's':
          target_linear_ = std::max(target_linear_.load() - linear_step_, -max_linear_);
          break;
        case 'a':
          steer_state_ = 1;  // full left — no partial angle
          break;
        case 'd':
          steer_state_ = -1;  // full right
          break;
        case 'c':
          steer_state_ = 0;  // straight wheels, keep current speed
          break;
        case ' ':
          target_linear_ = 0.0;
          steer_state_ = 0;
          break;
        case 'q':
          running_ = false;
          rclcpp::shutdown();
          break;
        default:
          break;
      }
    }

    tcsetattr(STDIN_FILENO, TCSANOW, &oldt);
  }

  double steer_to_angular() const
  {
    const int steer = steer_state_.load();
    if (steer > 0) {
      return max_angular_;
    }
    if (steer < 0) {
      return -max_angular_;
    }
    return 0.0;
  }

  void publish_cmd()
  {
    const double elapsed = (now() - last_key_time_).seconds();
    if (elapsed > timeout_sec_) {
      target_linear_ = 0.0;
      steer_state_ = 0;
    }

    geometry_msgs::msg::TwistStamped cmd;
    cmd.header.stamp = now();
    cmd.twist.linear.x = target_linear_.load();
    cmd.twist.angular.z = steer_to_angular();
    pub_->publish(cmd);
  }

  void publish_stop()
  {
    geometry_msgs::msg::TwistStamped cmd;
    cmd.header.stamp = now();
    pub_->publish(cmd);
  }

  rclcpp::Publisher<geometry_msgs::msg::TwistStamped>::SharedPtr pub_;
  rclcpp::TimerBase::SharedPtr timer_;
  std::thread keyboard_thread_;
  std::atomic<bool> running_{true};
  std::atomic<double> target_linear_{0.0};
  std::atomic<int> steer_state_{0};  // -1 right, 0 straight, +1 left
  rclcpp::Time last_key_time_;
  double max_linear_{};
  double max_angular_{};
  double linear_step_{};
  double timeout_sec_{};
};

int main(int argc, char ** argv)
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<TeleopNode>());
  rclcpp::shutdown();
  return 0;
}
