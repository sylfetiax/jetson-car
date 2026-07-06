#include <algorithm> // std::clamp (C++17) to limit velocity to parameter ranges
#include <chrono> // chrono types (included for consistency; timer not used in skeleton)
#include <memory> // std::make_shared, std::shared_ptr
#include <string> // std::string for parameter types
#include <thread>
#include <atomic>

#include "geometry_msgs/msg/twist.hpp" // Twist message for /cmd_vel velocity commands
#include "lifecycle_msgs/msg/state.hpp" // State constants: PRIMARY_STATE_ACTIVE, etc.
#include "rclcpp/rclcpp.hpp" // core ROS 2 C++ API
#include "rclcpp/executors/multi_threaded_executor.hpp" // MultiThreadedExecutor for parallel callbacks
#include "rclcpp_lifecycle/lifecycle_node.hpp" // LifecycleNode base class
#include "rcl_interfaces/msg/parameter_descriptor.hpp" // ParameterDescriptor, FloatingPointRange

#include <unistd.h>
#include <termios.h>

using CallbackReturn = rclcpp_lifecycle::node_interfaces::LifecycleNodeInterface::CallbackReturn; // SUCCESS/FAILURE
using State = lifecycle_msgs::msg::State; // shorthand for state ID constants
std::atomic<bool> running {true};

class TeleopLifecycle : public rclcpp_lifecycle::LifecycleNode // inherit from LifecycleNode, not Node
{
public:
  TeleopLifecycle()
  : LifecycleNode("teleop_lifecycle") // register lifecycle node name with ROS graph
  {
    declare_parameter<bool>("publish_test_on_activate", false); // test flag: publish one Twist on activate
  }

  CallbackReturn on_configure(const rclcpp_lifecycle::State &) // called on configure transition
  {
    RCLCPP_INFO(get_logger(), "Configuring..."); // log state change for debugging

    rcl_interfaces::msg::ParameterDescriptor linear_desc; // descriptor for max_linear param
    linear_desc.description = "Maximum linear speed (m/s)"; // visible in ros2 param describe
    rcl_interfaces::msg::FloatingPointRange linear_range; // allowed range object
    linear_range.from_value = 0.0; // min speed: 0 m/s
    linear_range.to_value = 1.0; // max speed: 1 m/s (safe default for tutorial car)
    linear_range.step = 0.1; // suggested slider step
    linear_desc.floating_point_range = {linear_range}; // attach range to descriptor
    declare_parameter<double>("max_linear", 0.5, linear_desc); // declare with default 0.5 and validation

    rcl_interfaces::msg::ParameterDescriptor angular_desc; // descriptor for max_angular param
    angular_desc.description = "Maximum angular speed (rad/s)"; // turning speed limit
    rcl_interfaces::msg::FloatingPointRange angular_range; // allowed range for angular velocity
    angular_range.from_value = 0.0; // no negative limit on magnitude (clamp handles sign)
    angular_range.to_value = 2.0; // max 2 rad/s rotation
    angular_range.step = 0.1; // suggested slider step
    angular_desc.floating_point_range = {angular_range}; // attach range
    declare_parameter<double>("max_angular", 1.0, angular_desc); // default 1.0 rad/s

    pub_ = create_publisher<geometry_msgs::msg::Twist>("/cmd_vel", 10); // lifecycle publisher on /cmd_vel
    return CallbackReturn::SUCCESS; // transition succeeded; move to Inactive
  }

  CallbackReturn on_activate(const rclcpp_lifecycle::State &) // called on activate transition
  {
    RCLCPP_INFO(get_logger(), "Activating..."); // log activation
    pub_->on_activate(); // MUST call this or publish() silently drops messages

    // if (get_parameter("publish_test_on_activate").as_bool()) { // optional test publish for verification
    //   publish_twist(get_parameter("max_linear").as_double(), 0.0); // forward at max speed
    //   RCLCPP_INFO(get_logger(), "Published test forward command"); // confirm test publish
    // }
    return CallbackReturn::SUCCESS; // now Active
  }

  CallbackReturn on_deactivate(const rclcpp_lifecycle::State &) // called on deactivate transition
  {
    RCLCPP_INFO(get_logger(), "Deactivating..."); // log deactivation
    geometry_msgs::msg::Twist stop; // default-constructed Twist: all zeros
    pub_->publish(stop); // send stop command before deactivating publisher
    pub_->on_deactivate(); // gate publisher; further publish() calls are dropped
    RCLCPP_INFO(get_logger(), "Published stop command"); // confirm stop sent
    return CallbackReturn::SUCCESS; // now Inactive
  }

  CallbackReturn on_cleanup(const rclcpp_lifecycle::State &) // called on cleanup transition
  {
    RCLCPP_INFO(get_logger(), "Cleaning up..."); // log cleanup
    pub_.reset(); // destroy publisher; release DDS resources
    return CallbackReturn::SUCCESS; // now Unconfigured
  }

  CallbackReturn on_shutdown(const rclcpp_lifecycle::State &) // called on shutdown transition
  {
    RCLCPP_INFO(get_logger(), "Shutting down..."); // log shutdown
    return CallbackReturn::SUCCESS; // now Finalized
  }

  void publish_twist(double linear, double angular) // public method for keyboard thread (homework)
  {
    // if (get_current_state().id() != State::PRIMARY_STATE_ACTIVE) { // safety check: only publish when active
    //   RCLCPP_WARN(get_logger(), "Not active — ignoring command"); // warn if called in wrong state
    //   return; // silently reject (with warning) instead of publishing
    // }
    const double max_lin = get_parameter("max_linear").as_double(); // read current speed limit
    const double max_ang = get_parameter("max_angular").as_double(); // read current turn limit
    geometry_msgs::msg::Twist cmd; // construct velocity command
    cmd.linear.x = std::clamp(linear, -max_lin, max_lin); // clamp to [-max, +max]
    cmd.angular.z = std::clamp(angular, -max_ang, max_ang); // clamp rotation
    pub_->publish(cmd); // send clamped command (only works when publisher is active)
  }

private:
  rclcpp_lifecycle::LifecyclePublisher<geometry_msgs::msg::Twist>::SharedPtr pub_; // lifecycle-gated publisher
};

void keyboard_work(std::shared_ptr<TeleopLifecycle> node) {

  while (running &&
    node->get_current_state().id() != State::PRIMARY_STATE_ACTIVE)
  {
    std::this_thread::sleep_for(std::chrono::milliseconds(50));
  }

  if (!running) {
    return;
  }

  if (!isatty(STDIN_FILENO)) {
    RCLCPP_ERROR(
      node->get_logger(),
      "stdin is not a terminal — keyboard teleop cannot work here. "
      "Use 'ros2 run jetson_car_control teleop_lifecycle' or launch with xterm "
      "(see teleop.launch.py).");
    return;
  }

  termios old_settings{};
  if (tcgetattr(STDIN_FILENO, &old_settings) != 0) {
    RCLCPP_ERROR(node->get_logger(), "tcgetattr failed — cannot configure keyboard input");
    return;
  }

  termios raw = old_settings;
  raw.c_lflag &= ~(ICANON | ECHO);
  raw.c_cc[VMIN] = 0;
  raw.c_cc[VTIME] = 1;  // 100 ms read timeout so SIGINT can stop the loop
  tcsetattr(STDIN_FILENO, TCSANOW, &raw);

  char c;
  while (running) {
    if (read(STDIN_FILENO, &c, 1) != 1) {
      continue;
    }

    const double max_linear = node->get_parameter("max_linear").as_double();
    const double max_angular = node->get_parameter("max_angular").as_double();

    switch (c) {
      case 'w':
        node->publish_twist(max_linear, 0);
        break;
      case 's':
        node->publish_twist(-max_linear, 0);
        break;
      case 'a':
        node->publish_twist(0, max_angular);
        break;
      case 'd':
        node->publish_twist(0, -max_angular);
        break;
      case ' ':
        node->publish_twist(0, 0);
        break;
      case 'q':
        node->publish_twist(0, 0);
        node->deactivate();
        tcsetattr(STDIN_FILENO, TCSANOW, &old_settings);
        rclcpp::shutdown();
        running = false;
        break;
      default:
        break;
      
    }
  }

  tcsetattr(STDIN_FILENO, TCSANOW, &old_settings);
}

int main(int argc, char * argv[]) // entry point
{
  rclcpp::init(argc, argv); // init ROS 2
  rclcpp::on_shutdown([]() { running = false; });
  auto node = std::make_shared<TeleopLifecycle>(); // create lifecycle node

  rclcpp::executors::MultiThreadedExecutor executor(rclcpp::ExecutorOptions(), 4); // 4-thread executor
  executor.add_node(node->get_node_base_interface()); // register lifecycle node with executor
  std::thread keyboard_thread(keyboard_work, node);
  executor.spin(); // block; process lifecycle service + future callbacks
  keyboard_thread.join();
  rclcpp::shutdown(); // cleanup
  return 0;
}
