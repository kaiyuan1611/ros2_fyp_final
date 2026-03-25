# Quick Start Guide - 3D Mapping

## Installation (One-time setup)

```bash
# Install Octomap (on Raspberry Pi)
sudo apt update
sudo apt install ros-humble-octomap-server ros-humble-octomap-msgs

# Build workspace
cd ~/ros2_fyp
colcon build
source install/setup.bash
```

## Running 3D Mapping (Modular Approach)

Each component runs in a separate terminal for maximum flexibility.

### Terminal 1: Base Robot System
```bash
cd ~/ros2_fyp
source install/setup.bash
ros2 launch r2_bringup bringup.launch.py
```
This starts:
✓ Robot description and TF
✓ Wheel odometry
✓ RPLidar A1
✓ Motor driver

### Terminal 2: Astra Camera
```bash
cd ~/ros2_fyp
source install/setup.bash
ros2 launch r2_bringup astra_camera.launch.py
```
This starts:
✓ Astra camera driver
✓ Point cloud generation

### Terminal 3: SLAM Toolbox (2D Mapping)
```bash
cd ~/ros2_fyp
source install/setup.bash
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=$PWD/config/mapper_params_online_async.yaml
```
This starts:
✓ 2D SLAM and localization
✓ 2D map generation

### Terminal 4: Octomap (3D Mapping)
```bash
cd ~/ros2_fyp
source install/setup.bash
ros2 launch r2_bringup octomap.launch.py
```
This starts:
✓ 3D occupancy grid mapping

### Terminal 5: Robot Control
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

### Visualize on Your Laptop (via SSH)

On your laptop (not the Pi), run RViz with X11 forwarding or use the RViz config:

**Option A: X11 Forwarding (if SSH with -X)**
```bash
# On laptop, SSH with X11 forwarding
ssh -X pi@<raspberry_pi_ip>
rviz2 -d ~/ros2_fyp/config/3d_mapping.rviz
```

**Option B: Native RViz on Laptop**
```bash
# On laptop, set ROS_DOMAIN_ID to match Pi
export ROS_DOMAIN_ID=0  # Match your Pi's domain ID
rviz2
```

**RViz Setup:**
1. Set Fixed Frame: `map`
2. Add displays:
   - RobotModel
   - LaserScan → Topic: `/scan`
   - Map → Topic: `/map` (2D map)
   - PointCloud2 → Topic: `/camera/depth/points`
   - MarkerArray → Topic: `/occupied_cells_vis_array` (3D map)

## How It Works

```
Terminal 1: RPLidar A1 → SLAM Toolbox → 2D Map + Robot Pose
Terminal 2: Astra Camera → Point Cloud
Terminal 3: Octomap → 3D Map (uses pose from SLAM)
```

**Key Points:**
- SLAM Toolbox provides accurate localization using the 2D laser
- Octomap uses this localization to build a 3D map from depth camera
- Both maps share the same coordinate frame (`map`)
- Lower computational cost than full 3D SLAM
- Modular design allows starting/stopping components independently

## Launch Order

Start in this order for best results:
1. Base robot system (bringup.launch.py)
2. Astra camera (astra_camera.launch.py)
3. SLAM Toolbox (wait ~5 seconds for initialization)
4. Octomap (after SLAM has started publishing TF)
5. Teleop for control

## Adjustments Needed

### 1. Camera Position (IMPORTANT!)
Measure where your Astra camera is mounted and update:
`src/r2_description/urdf/r2.urdf.xacro`

```xml
<!-- Line ~27 -->
<origin xyz="0.10 0.00 0.15" rpy="0 0 0"/>
```
- xyz: [forward, left, up] from base_link center
- rpy: [roll, pitch, yaw] rotation

After changing, rebuild:
```bash
colcon build --packages-select r2_description
source install/setup.bash
```

### 2. Octomap Resolution
For faster mapping or less memory:
`src/r2_bringup/launch/octomap.launch.py`

Change `resolution: 0.05` to `0.1` (larger = less detail, faster)

## Saving Your Maps

### 2D Map
```bash
ros2 run nav2_map_server map_saver_cli -f my_2d_map
```
Creates: `my_2d_map.pgm` and `my_2d_map.yaml`

### 3D Map
```bash
ros2 service call /octomap_server/save_map octomap_msgs/srv/SaveMap "{filename: 'my_3d_map.ot'}"
```
Creates: `my_3d_map.ot` (binary octomap file)

## Common Issues

**"No transform from camera_depth_optical_frame to map"**
- Wait a few seconds for SLAM to initialize
- Drive the robot a bit to build initial map

**Point cloud not visible in RViz**
- Check: `ros2 topic echo /camera/depth/points --no-arr` (on Pi)
- Verify camera is connected: `lsusb | grep Orbbec` (on Pi)

**Octomap is empty**
- Make sure SLAM Toolbox is running first
- Check TF: `ros2 run tf2_tools view_frames` (on Pi)
- Verify camera frame is correct in URDF

**RViz not connecting to Pi**
- Ensure both devices are on same network
- Check ROS_DOMAIN_ID matches on both machines
- Verify firewall allows ROS2 traffic (UDP ports)

## Next Steps

1. ✓ Test basic 3D mapping
2. Tune Octomap parameters for your environment
3. Add point cloud filtering (remove noise)
4. Integrate with Nav2 for autonomous navigation
5. Consider running RViz on laptop for better performance

See `3D_MAPPING_SETUP.md` for detailed documentation.
