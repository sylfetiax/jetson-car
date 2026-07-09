# jetson-car

ROS 2 workspace for a small Ackermann-steering car. Development on Ubuntu 24.04 with Jazzy; the onboard computer will use a native build from the same `src/`.

Hardware: TBA.

## Packages

| Package | Status | Description |
|---------|--------|-------------|
| `jetson_car` | working | Basic C++ nodes — talker/listener demo, `speed_talker` publishing `/cmd_vel` |
| `jetson_car_control` | working | Lifecycle keyboard teleop, `fake_odom` (circular path + tf), launch + RViz configs |
| `jetson_car_description` | working | URDF/Xacro model, RViz display launch |
| `jetson_car_bringup` | working | Gazebo Harmonic sim, world + spawn launch files |
| `jetson_car_perception` | planned | Camera, VO, sensor fusion |

## Requirements

- Ubuntu 24.04
- ROS 2 Jazzy (`/opt/ros/jazzy`)
- `colcon`, `rosdep`
- For teleop launch: `xterm` (`sudo apt install xterm`)
- For simulation: `ros-jazzy-ros-gz-sim`, `ros-jazzy-ros-gz-bridge`

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

**URDF in RViz**

```bash
ros2 launch jetson_car_description display.launch.py
```

**Gazebo simulation**

```bash
ros2 launch jetson_car_bringup sim.launch.py
ros2 launch jetson_car_bringup sim.launch.py x:=1.0 y:=0.5   # optional spawn offset
```

**RViz with sim time** (with `sim.launch.py` running in another terminal)

```bash
ros2 run rviz2 rviz2 \
  -d $(ros2 pkg prefix jetson_car_bringup)/share/jetson_car_bringup/config/sim.rviz \
  --ros-args -p use_sim_time:=true
```

## Roadmap

- [x] Basic ROS 2 C++ nodes and parameters
- [x] Lifecycle-managed teleop with clamped `/cmd_vel`
- [x] Fake odometry publisher + static sensor frames in tf
- [x] URDF model (chassis, wheels, camera, IMU)
- [x] Gazebo sim + `ros_gz` bridge
- [x] Ackermann `ros2_control` in simulation
- [x] Camera + IMU in sim, rosbag recording
- [x] Visual odometry + evaluation
- [ ] EKF fusion (wheel/VO/IMU)
- [ ] Motor bridge on Jetson GPIO, camera as ROS topic
- [ ] On-robot VO, WiFi teleop, supervised driving tests
- [ ] Unit tests + CI

## Current repo layout

Only `src/` is tracked. Build artifacts stay local:

```
car_ws/
├── LICENSE
├── README.md
├── jetson_car_bringup/              # ament_python — sim bringup
│   ├── config/
│   │   └── sim.rviz                 # RViz config for Gazebo
│   ├── launch/
│   │   ├── gz_world.launch.py       # empty Gazebo world
│   │   └── sim.launch.py            # world + spawn + clock bridge
│   ├── worlds/
│   │   └── empty.sdf                # ground-plane world
│   ├── package.xml
│   └── setup.py
├── src/
│   ├── jetson_car/                  # ament_cmake — C++ learning nodes
│   │   └── src/                     # talker, listener, speed_talker
│   ├── jetson_car_control/          # ament_cmake — teleop, fake odom
│   │   ├── launch/
│   │   ├── rviz/
│   │   └── src/
│   └── jetson_car_description/      # ament_cmake — robot model
│       ├── config/display.rviz
│       ├── launch/display.launch.py
│       ├── urdf/jetson_car.urdf.xacro
│       └── DIMENSIONS.md
├── build/                           # gitignored
├── install/                         # gitignored
└── log/                             # gitignored
```

## License

MIT
