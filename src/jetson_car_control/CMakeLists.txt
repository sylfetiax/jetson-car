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
find_package(nav_msgs REQUIRED) 
find_package(tf2 REQUIRED) 
find_package(tf2_ros REQUIRED)

add_executable(teleop_lifecycle src/teleop_lifecycle.cpp) # build teleop_lifecycle binary
ament_target_dependencies(teleop_lifecycle # link against ROS dependencies
  rclcpp rclcpp_lifecycle lifecycle_msgs geometry_msgs)

add_executable(fake_odom src/fake_odom.cpp)
ament_target_dependencies(fake_odom
  rclcpp nav_msgs geometry_msgs tf2 tf2_ros)

add_executable(drive_commander src/drive_commander.cpp)
ament_target_dependencies(drive_commander rclcpp geometry_msgs)

add_executable(teleop src/teleop.cpp)
ament_target_dependencies(teleop rclcpp geometry_msgs)

install(TARGETS teleop_lifecycle DESTINATION lib/${PROJECT_NAME}) # install for ros2 run
install(DIRECTORY launch DESTINATION share/${PROJECT_NAME}) # install launch files when they exist
install(TARGETS fake_odom drive_commander teleop DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY rviz DESTINATION share/${PROJECT_NAME} OPTIONAL) 

ament_package() # finalize; must be last