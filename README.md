# jetson-car

ROS 2 workspace for a small Ackermann-steering car. Development on Ubuntu 24.04 with Jazzy; the onboard computer will use a native build from the same `src/`.

Hardware: TBA.

## Packages

| Package | Status | Description |
|---------|--------|-------------|
| `jetson_car` | working | Basic C++ nodes — talker/listener demo, `speed_talker` publishing `/cmd_vel` |
| `jetson_car_control` | working | Lifecycle keyboard teleop, `fake_odom` (circular path + tf), launch + RViz configs |
| `jetson_car_description` | planned | URDF/Xacro robot model |
| `jetson_car_bringup` | planned | Sim + hardware launch files |
| `jetson_car_perception` | planned | Camera, VO, sensor fusion |

## Requirements

- Ubuntu 24.04
- ROS 2 Jazzy (`/opt/ros/jazzy`)
- `colcon`, `rosdep`
- For teleop launch: `xterm` (`sudo apt install xterm`)

## Build

```bash
source /opt/ros/jazzy/setup.bash
cd car_ws
colcon build --symlink-install
source install/setup.bash
export ROS_DOMAIN_ID=42   # change if you share a network with other ROS users
```

Single package:

```bash
colcon build --packages-select jetson_car_control --symlink-install
```

## Run

**Pub/sub demo**

```bash
ros2 run jetson_car talker
ros2 run jetson_car listener
```

**Keyboard teleop** (`w`/`a`/`s`/`d`, space = stop, `q` = quit)

```bash
ros2 run jetson_car_control teleop_lifecycle
ros2 lifecycle set /teleop_lifecycle configure
ros2 lifecycle set /teleop_lifecycle activate
```

Or via launch (opens a separate xterm for keyboard input):

```bash
ros2 launch jetson_car_control teleop.launch.py
```

**Odometry + tf test**

```bash
ros2 launch jetson_car_control odom_demo.launch.py
ros2 run tf2_ros tf2_echo odom base_link
```

## Roadmap

- [x] Basic ROS 2 C++ nodes and parameters
- [x] Lifecycle-managed teleop with clamped `/cmd_vel`
- [x] Fake odometry publisher + static sensor frames in tf
- [ ] URDF model (chassis, wheels, camera, IMU)
- [ ] Gazebo sim + `ros_gz` bridge
- [ ] Ackermann `ros2_control` in simulation
- [ ] Camera + IMU in sim, rosbag recording
- [ ] Visual odometry + evaluation
- [ ] EKF fusion (wheel/VO/IMU)
- [ ] Motor bridge on Jetson GPIO, camera as ROS topic
- [ ] On-robot VO, WiFi teleop, supervised driving tests
- [ ] Unit tests + CI

## Repo layout

Only `src/` is tracked. Build artifacts stay local:

```
car_ws/
├── src/
│   ├── jetson_car/
│   └── jetson_car_control/
├── build/ install/ log/   # gitignored
└── README.md
```

## License

MIT
