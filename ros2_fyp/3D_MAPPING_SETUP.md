# 3D Mapping Setup with Octomap + SLAM Toolbox

## Overview
This setup combines:
- **SLAM Toolbox**: 2D SLAM for localization and 2D map generation using RPLidar A1
- **Octomap**: 3D occupancy grid mapping using Astra depth camera
- **Sensor Fusion**: Uses SLAM Toolbox's localization to position 3D points from the depth camera

## Prerequisites

### 1. Install Octomap Server (on Raspberry Pi)
```bash
sudo apt update
sudo apt install ros-humble-octomap-server ros-humble-octomap-msgs
```

Note: `ros-humble-octomap-rviz-plugins` is only needed on the machine running RViz (your laptop).

### 2. Verify Astra Camera Installation
The Astra camera package is already in your workspace. Make sure it's built:
```bash
cd ~/ros2_fyp
colcon build --packages-select astra_camera astra_camera_msgs
source install/setup.bash
```

### 3. Network Setup for Remote Visualization
If running RViz on your laptop while the robot runs on Pi:

**On Raspberry Pi:**
```bash
# Check/set ROS_DOMAIN_ID (default is 0)
echo $ROS_DOMAIN_ID
export ROS_DOMAIN_ID=0  # Add to ~/.bashrc to persist
```

**On Laptop:**
```bash
# Install ROS2 Humble (if not already installed)
# Set matching ROS_DOMAIN_ID
export ROS_DOMAIN_ID=0  # Must match Pi

# Install RViz plugins
sudo apt install ros-humble-rviz2 ros-humble-octomap-rviz-plugins
```

## Hardware Setup

### Camera Mounting Position
Update the camera position in `src/r2_description/urdf/r2.urdf.xacro`:
```xml
<origin xyz="0.10 0.00 0.15" rpy="0 0 0"/>
```
Adjust the values based on your actual mounting:
- `xyz`: [forward, left, up] in meters from base_link
- `rpy`: [roll, pitch, yaw] in radians

### TF Tree Structure
```
map -> odom -> base_footprint -> base_link -> camera_link -> camera_depth_optical_frame
                                           -> laser
```

## Usage

### Modular Launch (Recommended for SSH Setup)

Run each component in a separate terminal on the Raspberry Pi:

**Terminal 1 - Base robot:**
```bash
cd ~/ros2_fyp
source install/setup.bash
ros2 launch r2_bringup bringup.launch.py
```

**Terminal 2 - Astra camera:**
```bash
cd ~/ros2_fyp
source install/setup.bash
ros2 launch r2_bringup astra_camera.launch.py
```

**Terminal 3 - SLAM Toolbox:**
```bash
cd ~/ros2_fyp
source install/setup.bash
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=$PWD/config/mapper_params_online_async.yaml
```

**Terminal 4 - Octomap:**
```bash
cd ~/ros2_fyp
source install/setup.bash
ros2 launch r2_bringup octomap.launch.py
```

**Terminal 5 - Robot Control:**
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

### Visualization on Laptop

**On your laptop (not the Pi):**

```bash
# Set ROS_DOMAIN_ID to match Pi
export ROS_DOMAIN_ID=0

# Source ROS2
source /opt/ros/humble/setup.bash

# Launch RViz
rviz2
```

Or use the pre-configured setup:
```bash
# Copy config from Pi to laptop first (one-time)
scp pi@<pi_ip>:~/ros2_fyp/config/3d_mapping.rviz ~/

# Then launch
rviz2 -d ~/3d_mapping.rviz
```

Add these displays:
1. **RobotModel** - Shows your robot
2. **TF** - Shows coordinate frames
3. **LaserScan** - Topic: `/scan` (RPLidar data)
4. **Map** - Topic: `/map` (2D map from SLAM Toolbox)
5. **PointCloud2** - Topic: `/camera/depth/points` (Astra point cloud)
6. **MarkerArray** - Topic: `/occupied_cells_vis_array` (Octomap 3D visualization)
7. **Map** - Topic: `/projected_map` (2D projection of 3D map)

Set Fixed Frame to: `map`

## Topic Reference

### Astra Camera Topics
- `/camera/color/image_raw` - RGB image
- `/camera/depth/image_raw` - Depth image
- `/camera/depth/points` - 3D point cloud (used by Octomap)
- `/camera/color/camera_info` - Camera calibration

### SLAM Toolbox Topics
- `/scan` - Input from RPLidar
- `/map` - 2D occupancy grid
- `/map_metadata` - Map information

### Octomap Topics
- `/octomap_binary` - Binary octomap (compact)
- `/octomap_full` - Full octomap
- `/occupied_cells_vis_array` - Visualization markers
- `/projected_map` - 2D projection for navigation

## Configuration

### Octomap Parameters
Edit `src/r2_bringup/launch/octomap.launch.py`:
- `resolution`: Voxel size (0.05 = 5cm cubes)
- `sensor_model.max_range`: Max depth range (5.0m for Astra)
- `sensor_model.min_range`: Min depth range (0.3m)
- `filter_ground`: Enable/disable ground filtering

### SLAM Toolbox Parameters
Edit `config/mapper_params_online_async.yaml`:
- Already configured for your RPLidar A1
- No changes needed for Octomap integration

## Saving Maps

### Save 2D Map (SLAM Toolbox)
```bash
# On Raspberry Pi
cd ~/ros2_fyp
ros2 run nav2_map_server map_saver_cli -f my_2d_map
```

### Save 3D Map (Octomap)
```bash
# On Raspberry Pi
ros2 service call /octomap_server/save_map octomap_msgs/srv/SaveMap "{filename: 'my_3d_map.ot'}"
```

Maps will be saved in the current directory on the Pi. You can copy them to your laptop:
```bash
# On laptop
scp pi@<pi_ip>:~/ros2_fyp/my_2d_map.* ~/maps/
scp pi@<pi_ip>:~/ros2_fyp/my_3d_map.ot ~/maps/
```

## Troubleshooting

### No point cloud visible
1. Check camera is connected (on Pi): `ros2 topic list | grep camera`
2. Check TF tree (on Pi): `ros2 run tf2_tools view_frames`
3. Verify point cloud data (on Pi): `ros2 topic echo /camera/depth/points --no-arr`

### Octomap not building
1. Verify SLAM Toolbox is running and publishing TF (on Pi)
2. Check frame_id matches (on Pi): `ros2 topic info /camera/depth/points`
3. Ensure camera_depth_optical_frame is in TF tree (on Pi)

### TF errors
1. Make sure robot_state_publisher is running (part of bringup.launch.py)
2. Verify URDF is correct (on Pi): `ros2 run robot_state_publisher robot_state_publisher --ros-args -p robot_description:="$(xacro ~/ros2_fyp/src/r2_description/urdf/r2.urdf.xacro)"`

### Camera position is wrong
Update the camera mounting position in `src/r2_description/urdf/r2.urdf.xacro` and rebuild:
```bash
cd ~/ros2_fyp
colcon build --packages-select r2_description
source install/setup.bash
```

### RViz on laptop not showing data
1. Verify network connectivity: `ping <pi_ip>`
2. Check ROS_DOMAIN_ID matches on both machines
3. Test topic visibility from laptop: `ros2 topic list`
4. Check firewall settings (ROS2 uses UDP multicast)
5. Ensure both machines are on same subnet

### SSH session management
Use `tmux` or `screen` to manage multiple terminals:
```bash
# Install tmux
sudo apt install tmux

# Start tmux session
tmux new -s mapping

# Split windows: Ctrl+b then "
# Switch panes: Ctrl+b then arrow keys
# Detach: Ctrl+b then d
# Reattach: tmux attach -t mapping
```

## Performance Tips

1. **Reduce resolution** if mapping is slow: Change `resolution: 0.1` in octomap.launch.py
2. **Limit max range** to reduce processing: Adjust `sensor_model.max_range: 3.0`
3. **Filter ground plane** if not needed: Set `filter_ground: True`

## Next Steps

1. Test camera mounting and adjust URDF positions
2. Calibrate camera if needed
3. Tune Octomap parameters for your environment
4. Integrate with Nav2 for 3D obstacle avoidance
5. Consider adding point cloud filtering for better maps
