cmake_minimum_required(VERSION 3.8) # minimum CMake version; ROS 2 Jazzy requires 3.8+
project(jetson_car) # project name; sets ${PROJECT_NAME} used below


if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang") # if GCC or Clang compiler
  add_compile_options(-Wall -Wextra -Wpedantic) # enable strict warnings: catch bugs at compile time
endif()

find_package(ament_cmake REQUIRED) # ament build system macros (ament_package, install rules)
find_package(rclcpp REQUIRED) # locate rclcpp headers and libraries for linking
find_package(std_msgs REQUIRED) # locate std_msgs headers (String message)
find_package(geometry_msgs REQUIRED) # for homework speed_talker (Twist message)
find_package(example_interfaces REQUIRED) # for homework service (Trigger srv)

add_executable(talker src/talker.cpp) # compile talker.cpp into executable named "talker"
ament_target_dependencies(talker rclcpp std_msgs) # link talker against rclcpp and std_msgs

add_executable(speed_talker src/speed_talker.cpp)
ament_target_dependencies(speed_talker rclcpp geometry_msgs)

add_executable(listener src/listener.cpp) # compile listener.cpp into executable named "listener"
ament_target_dependencies(listener rclcpp std_msgs) # link listener against rclcpp and std_msgs

install(TARGETS talker speed_talker listener DESTINATION lib/${PROJECT_NAME}) # install binaries so ros2 run finds them

ament_package() # finalize package; must be last call in CMakeLists.txt
