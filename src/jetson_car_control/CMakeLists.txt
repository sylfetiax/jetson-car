cmake_minimum_required(VERSION 3.8) # minimum CMake version
project(jetson_car_control) # project and package name


if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang") # GCC or Clang
  add_compile_options(-Wall -Wextra -Wpedantic) # strict warnings
endif()

find_package(ament_cmake REQUIRED) # ament build system
find_package(rclcpp REQUIRED) # core client library
find_package(rclcpp_lifecycle REQUIRED) # lifecycle node support
find_package(lifecycle_msgs REQUIRED) # state/transition messages
find_package(geometry_msgs REQUIRED) # Twist message

add_executable(teleop_lifecycle src/teleop_lifecycle.cpp) # build teleop_lifecycle binary
ament_target_dependencies(teleop_lifecycle # link against ROS dependencies
  rclcpp rclcpp_lifecycle lifecycle_msgs geometry_msgs)

install(TARGETS teleop_lifecycle DESTINATION lib/${PROJECT_NAME}) # install for ros2 run
install(DIRECTORY launch DESTINATION share/${PROJECT_NAME}) # install launch files when they exist

ament_package() # finalize; must be last