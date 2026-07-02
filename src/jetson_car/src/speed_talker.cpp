#include <chrono>
#include <memory>
#include <string>

#include "rclcpp/rclcpp.hpp"
#include "geometry_msgs/msg/twist.hpp"

using namespace std::chrono_literals;

class SpeedTalker : public rclcpp::Node {
	public:
	  SpeedTalker() : Node("speed_talker") {
		declare_parameter<double>("max_speed", 1.0);
		declare_parameter<double>("publish_rate", 2.0);
		speed_ = get_parameter("max_speed").as_double();
	
		param_callback_handle_ = add_on_set_parameters_callback(
		  [this](const std::vector<rclcpp::Parameter> & params) {
			rcl_interfaces::msg::SetParametersResult result;
			result.successful = true;
	
			for (const auto & p : params) {
			  if (p.get_name() == "max_speed") {
				if (p.get_type() != rclcpp::ParameterType::PARAMETER_DOUBLE) {
				  result.successful = false;
				  result.reason = "max_speed must be a double";
				  return result;
				}
				speed_ = p.as_double();
			  } else if (p.get_name() == "publish_rate") {
				if (p.get_type() != rclcpp::ParameterType::PARAMETER_DOUBLE) {
				  result.successful = false;
				  result.reason = "publish_rate must be a double";
				  return result;
				}
				if (p.as_double() <= 0.0) {
				  result.successful = false;
				  result.reason = "publish_rate must be > 0";
				  return result;
				}
				reset_timer(p.as_double());
			  }
			}
			return result;
		  });
	
		publisher_ = create_publisher<geometry_msgs::msg::Twist>("cmd_vel", 10);
		reset_timer(get_parameter("publish_rate").as_double());
	  }
	
	private:
	  void reset_timer(double rate) {
		auto period = std::chrono::duration<double>(1.0 / rate);
		timer_ = create_wall_timer(
		  std::chrono::duration_cast<std::chrono::milliseconds>(period),
		  [this]() {
			auto msg = geometry_msgs::msg::Twist();
			msg.linear.x = speed_;
			msg.angular.z = 0.0;
			publisher_->publish(msg);
			RCLCPP_INFO(get_logger(),
			  "Publishing: linear(%.2f, %.2f, %.2f), angular(%.2f, %.2f, %.2f)",
			  msg.linear.x, msg.linear.y, msg.linear.z,
			  msg.angular.x, msg.angular.y, msg.angular.z);
		  });
	  }
	
	  rclcpp::node_interfaces::OnSetParametersCallbackHandle::SharedPtr param_callback_handle_;
	  rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr publisher_;
	  rclcpp::TimerBase::SharedPtr timer_;
	  double speed_;
	};

int main (int argc, char *argv[]) {
	rclcpp::init(argc, argv);
	auto node = std::make_shared<SpeedTalker>();
	rclcpp::spin(node);
	rclcpp::shutdown();
	return 0;
}
