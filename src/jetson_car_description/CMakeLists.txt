cmake_minimum_required(VERSION 3.8)
project(jetson_car_description)


find_package(ament_cmake REQUIRED)

install(DIRECTORY urdf launch config meshes DESTINATION share/${PROJECT_NAME})

install(FILES DIMENSIONS.md DESTINATION share/${PROJECT_NAME})

ament_package()