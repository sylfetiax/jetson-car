# Dimensions


## Physical measurements

| Parameter | Sim value (m) | Measured (m) | Notes |
|-----------|---------------|--------------|-------|
| Wheelbase | 0.110 | | front axle to rear axle |
| Track width | 0.075 | | left to right wheel center |
| Wheel radius | 0.0151 | | tire diameter / 2 |
| Chassis L × W × H | 0.160 × 0.086 × 0.026 | | |
| Camera forward offset | 0.104 | | from base_link |
| Camera height | 0.068 | | above base_link |
| Max steer angle | 0.585 rad (~33.6°) | | |

## Validation

Run:

```bash
xacro urdf/jetson_car.urdf.xacro > /tmp/jetson_car.urdf
check_urdf /tmp/jetson_car.urdf

```

```
tson_car.urdf
robot name is: jetson_car
---------- Successfully Parsed XML ---------------
root Link: base_footprint has 1 child(ren)
    child(1):  base_link
        child(1):  camera_link
            child(1):  camera_optical_frame
        child(2):  front_left_knuckle
            child(1):  front_left_wheel
        child(3):  front_right_knuckle
            child(1):  front_right_wheel
        child(4):  imu_link
        child(5):  rear_left_wheel
        child(6):  rear_right_wheel
```