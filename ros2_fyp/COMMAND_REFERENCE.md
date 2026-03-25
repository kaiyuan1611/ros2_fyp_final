# Command Reference - 3D Mapping System

## Quick Start Commands (Modular Launch)

### On Raspberry Pi - Terminal 1: Base System
```bash
cd ~/ros2_fyp
source install/setup.bash
ros2 launch r2_bringup bringup.launch.py
```

### On Raspberry Pi - Terminal 2: Camera
```bash
cd ~/ros2_fyp
source install/setup.bash
ros2 launch r2_bringup astra_camera.launch.py
```

### On Raspberry Pi - Terminal 3: SLAM
```bash
cd ~/ros2_fyp
source install/setup.bash
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=$PWD/config/mapper_params_online_async.yaml
```

### On Raspberry Pi - Terminal 4: Octomap
```bash
cd ~/ros2_fyp
source install/setup.bash
ros2 launch r2_bringup octomap.launch.py
```

### On Raspberry Pi or Laptop - Terminal 5: Control
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

### On Laptop: Visualization
```bash
export ROS_DOMAIN_ID=0  # Match Pi's domain ID
source /opt/ros/humble/setup.bash
rviz2
```

## Building and Setup

### Build Workspace
```bash
cd ~/ros2_fyp
colcon build
source install/setup.bash
```

### Build Specific Packages
```bash
colcon build --packages-select r2_description r2_bringup
```

### Build with Symlink (faster for Python/launch files)
```bash
colcon build --symlink-install
```

### Clean Build
```bash
rm -rf build install log
colcon build
```

## Diagnostic Commands (Run on Raspberry Pi)

### List All Topics
```bash
ros2 topic list
```

### Check Topic Rate
```bash
ros2 topic hz /scan
ros2 topic hz /camera/depth/points
ros2 topic hz /map
ros2 topic hz /octomap_binary
```

### Echo Topic Data
```bash
# Laser scan
ros2 topic echo /scan

# Point cloud (without array data)
ros2 topic echo /camera/depth/points --no-arr

# Odometry
ros2 topic echo /odom

# Map metadata
ros2 topic echo /map_metadata
```

### Topic Information
```bash
ros2 topic info /scan
ros2 topic info /camera/depth/points
ros2 topic info /map
```

### List All Nodes
```bash
ros2 node list
```

### Node Information
```bash
ros2 node info /slam_toolbox
ros2 node info /octomap_server
ros2 node info /camera
```

### Check TF Tree
```bash
# Generate PDF of TF tree
ros2 run tf2_tools view_frames

# View specific transform
ros2 run tf2_ros tf2_echo map base_link
ros2 run tf2_ros tf2_echo base_link camera_depth_optical_frame
```

### Check Parameters
```bash
# List parameters for a node
ros2 param list /slam_toolbox
ros2 param list /octomap_server

# Get specific parameter
ros2 param get /octomap_server resolution
ros2 param get /slam_toolbox resolution
```

## Camera Commands

### List Camera Topics
```bash
ros2 topic list | grep camera
```

### View Camera Images
```bash
# RGB image
ros2 run rqt_image_view rqt_image_view /camera/color/image_raw

# Depth image
ros2 run rqt_image_view rqt_image_view /camera/depth/image_raw
```

### Check Camera Info
```bash
ros2 topic echo /camera/color/camera_info
ros2 topic echo /camera/depth/camera_info
```

### Test Camera Connection
```bash
lsusb | grep -i orbbec
# Should show: Orbbec 3D Technology Co., Ltd.
```

## Map Saving and Loading

### Save 2D Map
```bash
# Save to current directory
ros2 run nav2_map_server map_saver_cli -f my_map

# Save to specific location
ros2 run nav2_map_server map_saver_cli -f ~/maps/my_map

# With specific parameters
ros2 run nav2_map_server map_saver_cli -f my_map --occ 65 --free 25
```

### Save 3D Map (Octomap)
```bash
# Binary format (compact)
ros2 service call /octomap_server/save_map \
  octomap_msgs/srv/SaveMap "{filename: 'my_3d_map.ot'}"

# Full format (larger, more info)
ros2 service call /octomap_server/save_map \
  octomap_msgs/srv/SaveMap "{filename: 'my_3d_map.bt'}"
```

### Load 2D Map (for localization)
```bash
ros2 run nav2_map_server map_server --ros-args \
  -p yaml_filename:=my_map.yaml
```

## Octomap Services

### List Available Services
```bash
ros2 service list | grep octomap
```

### Reset Octomap
```bash
ros2 service call /octomap_server/reset std_srvs/srv/Empty
```

### Save Octomap
```bash
ros2 service call /octomap_server/save_map \
  octomap_msgs/srv/SaveMap "{filename: 'map.ot'}"
```

## SLAM Toolbox Services

### List SLAM Services
```bash
ros2 service list | grep slam
```

### Save SLAM Map
```bash
ros2 service call /slam_toolbox/save_map \
  slam_toolbox/srv/SaveMap "{name: {data: 'my_slam_map'}}"
```

### Serialize SLAM Map (with pose graph)
```bash
ros2 service call /slam_toolbox/serialize_map \
  slam_toolbox/srv/SerializePoseGraph "{filename: 'my_slam_session'}"
```

### Deserialize SLAM Map (continue mapping)
```bash
ros2 service call /slam_toolbox/deserialize_map \
  slam_toolbox/srv/DeserializePoseGraph \
  "{filename: 'my_slam_session', match_type: 1}"
```

## Visualization Commands

### Launch RViz (On Laptop)
```bash
# Set domain ID to match Pi
export ROS_DOMAIN_ID=0
source /opt/ros/humble/setup.bash

# With custom config (copy from Pi first)
rviz2 -d ~/3d_mapping.rviz

# Default config
rviz2
```

### Copy RViz Config from Pi (One-time)
```bash
# On laptop
scp pi@<pi_ip>:~/ros2_fyp/config/3d_mapping.rviz ~/
```

### View Images from Pi (On Laptop)
```bash
# RGB image
ros2 run rqt_image_view rqt_image_view /camera/color/image_raw

# Depth image
ros2 run rqt_image_view rqt_image_view /camera/depth/image_raw
```

### RQT Tools (Can run on laptop)
```bash
export ROS_DOMAIN_ID=0
source /opt/ros/humble/setup.bash

# Topic monitor
rqt_topic

# Graph view
rqt_graph

# Image view
rqt_image_view

# All tools
rqt
```

## Recording and Playback

### Record Bag File
```bash
# Record all topics
ros2 bag record -a

# Record specific topics
ros2 bag record /scan /camera/depth/points /odom /tf /tf_static

# Record with custom name
ros2 bag record -o my_mapping_session /scan /camera/depth/points /odom
```

### Play Bag File
```bash
ros2 bag play my_mapping_session

# Play at slower speed
ros2 bag play my_mapping_session --rate 0.5

# Play in loop
ros2 bag play my_mapping_session --loop
```

### Bag Info
```bash
ros2 bag info my_mapping_session
```

## Debugging Commands

### Check for Errors
```bash
# View logs
ros2 run rqt_console rqt_console

# Check specific node output
ros2 node info /slam_toolbox
```

### Monitor System Resources
```bash
# CPU and memory usage
htop

# ROS2 specific
ros2 wtf
```

### Test Individual Components

#### Test RPLidar
```bash
ros2 launch rplidar_ros rplidar_a1_launch.py
# In another terminal:
ros2 topic echo /scan
```

#### Test Astra Camera
```bash
ros2 launch r2_bringup astra_camera.launch.py
# In another terminal:
ros2 topic list | grep camera
```

#### Test Wheel Odometry
```bash
ros2 run r2_wheel_odometry wheel_odom
# In another terminal:
ros2 topic echo /odom
```

## Performance Monitoring

### Check Topic Bandwidth
```bash
ros2 topic bw /camera/depth/points
ros2 topic bw /scan
```

### Check Topic Delay
```bash
ros2 topic delay /camera/depth/points
```

### Monitor TF Delays
```bash
ros2 run tf2_ros tf2_monitor
```

## Parameter Tuning

### Change Octomap Resolution (runtime)
```bash
ros2 param set /octomap_server resolution 0.1
```

### Change SLAM Parameters (requires restart)
```bash
# Edit config file
nano ~/ros2_fyp/config/mapper_params_online_async.yaml
# Restart SLAM Toolbox
```

### List All Parameters
```bash
ros2 param list
```

## Network and Multi-Machine Setup

### Set ROS Domain ID (On Both Pi and Laptop)
```bash
# Add to ~/.bashrc for persistence
export ROS_DOMAIN_ID=0
```

### Check Network Configuration
```bash
ros2 doctor
```

### Test Topic Visibility from Laptop
```bash
# On laptop
export ROS_DOMAIN_ID=0
source /opt/ros/humble/setup.bash
ros2 topic list  # Should see topics from Pi
```

### Check Network Connectivity
```bash
# From laptop
ping <pi_ip>

# Check if ROS2 traffic is flowing
ros2 topic hz /scan  # Should show data from Pi
```

## Troubleshooting Commands

### Check USB Devices
```bash
# List all USB devices
lsusb

# Check specific device
lsusb | grep -i orbbec  # Camera
ls -l /dev/rplidar      # LiDAR
```

### Check Serial Permissions
```bash
# Add user to dialout group (for serial devices)
sudo usermod -a -G dialout $USER
# Logout and login for changes to take effect
```

### Fix TF Issues
```bash
# View TF tree
ros2 run tf2_tools view_frames

# Check specific transform
ros2 run tf2_ros tf2_echo map camera_depth_optical_frame

# Monitor TF
ros2 run tf2_ros tf2_monitor
```

### Check for Missing Dependencies
```bash
rosdep install --from-paths src --ignore-src -r -y
```

## Useful Aliases (add to ~/.bashrc on Pi)

```bash
# Add these to ~/.bashrc for convenience
alias ros2_fyp='cd ~/ros2_fyp && source install/setup.bash'
alias build_fyp='cd ~/ros2_fyp && colcon build && source install/setup.bash'
alias start_base='cd ~/ros2_fyp && source install/setup.bash && ros2 launch r2_bringup bringup.launch.py'
alias start_camera='cd ~/ros2_fyp && source install/setup.bash && ros2 launch r2_bringup astra_camera.launch.py'
alias start_slam='cd ~/ros2_fyp && source install/setup.bash && ros2 launch slam_toolbox online_async_launch.py slam_params_file:=$PWD/config/mapper_params_online_async.yaml'
alias start_octomap='cd ~/ros2_fyp && source install/setup.bash && ros2 launch r2_bringup octomap.launch.py'
alias teleop='ros2 run teleop_twist_keyboard teleop_twist_keyboard'
alias save2d='ros2 run nav2_map_server map_saver_cli -f'
alias save3d='ros2 service call /octomap_server/save_map octomap_msgs/srv/SaveMap'
```

After adding, reload:
```bash
source ~/.bashrc
```

## SSH and Terminal Management

### SSH with X11 Forwarding (if needed)
```bash
# From laptop
ssh -X pi@<pi_ip>
```

### Using tmux for Multiple Terminals
```bash
# On Pi, install tmux
sudo apt install tmux

# Start new session
tmux new -s mapping

# Split window horizontally
Ctrl+b then "

# Split window vertically
Ctrl+b then %

# Switch between panes
Ctrl+b then arrow keys

# Create new window
Ctrl+b then c

# Switch windows
Ctrl+b then 0-9

# Detach from session (keeps running)
Ctrl+b then d

# List sessions
tmux ls

# Reattach to session
tmux attach -t mapping

# Kill session
tmux kill-session -t mapping
```

### Using screen (Alternative to tmux)
```bash
# Start new session
screen -S mapping

# Create new window
Ctrl+a then c

# Switch windows
Ctrl+a then n (next) or p (previous)

# Detach
Ctrl+a then d

# Reattach
screen -r mapping
```

## Emergency Commands

### Kill All ROS Nodes
```bash
killall -9 ros2
```

### Kill Specific Node
```bash
ros2 node list
ros2 lifecycle set /node_name shutdown
```

### Reset Everything
```bash
# Kill all ROS processes
killall -9 ros2

# Clear build artifacts
cd ~/ros2_fyp
rm -rf build install log

# Rebuild
colcon build
source install/setup.bash
```

## Common Command Sequences

### Full Mapping Session (Using tmux on Pi)
```bash
# On Pi: Start tmux session
tmux new -s mapping

# Pane 1: Base system
cd ~/ros2_fyp && source install/setup.bash
ros2 launch r2_bringup bringup.launch.py

# Ctrl+b then " to split
# Pane 2: Camera
cd ~/ros2_fyp && source install/setup.bash
ros2 launch r2_bringup astra_camera.launch.py

# Ctrl+b then " to split
# Pane 3: SLAM
cd ~/ros2_fyp && source install/setup.bash
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=$PWD/config/mapper_params_online_async.yaml

# Ctrl+b then " to split
# Pane 4: Octomap
cd ~/ros2_fyp && source install/setup.bash
ros2 launch r2_bringup octomap.launch.py

# Detach: Ctrl+b then d
# Everything keeps running in background
```

### On Laptop: Visualization and Control
```bash
# Terminal 1: RViz
export ROS_DOMAIN_ID=0
source /opt/ros/humble/setup.bash
rviz2

# Terminal 2: Control
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# Terminal 3: Monitor (optional)
ros2 topic hz /map
ros2 topic hz /octomap_binary
```

### Save Maps (On Pi)
```bash
# Save 2D map
cd ~/ros2_fyp
ros2 run nav2_map_server map_saver_cli -f my_map

# Save 3D map
ros2 service call /octomap_server/save_map \
  octomap_msgs/srv/SaveMap "{filename: 'my_3d_map.ot'}"

# Copy to laptop
# On laptop:
scp pi@<pi_ip>:~/ros2_fyp/my_map.* ~/maps/
scp pi@<pi_ip>:~/ros2_fyp/my_3d_map.ot ~/maps/
```

### Quick Test Sequence (On Pi)
```bash
# Check hardware
lsusb | grep Orbbec
ls -l /dev/rplidar

# Check topics
ros2 topic list

# Check TF
ros2 run tf2_tools view_frames

# Check rates
ros2 topic hz /scan
ros2 topic hz /camera/depth/points
```

### Quick Test from Laptop
```bash
# Set domain ID
export ROS_DOMAIN_ID=0
source /opt/ros/humble/setup.bash

# Check connectivity
ros2 topic list

# Check data flow
ros2 topic hz /scan
ros2 topic echo /odom --no-arr
```

---

**Quick Reference Card**

| Task | Command | Where |
|------|---------|-------|
| Start base system | `ros2 launch r2_bringup bringup.launch.py` | Pi |
| Start camera | `ros2 launch r2_bringup astra_camera.launch.py` | Pi |
| Start SLAM | `ros2 launch slam_toolbox online_async_launch.py slam_params_file:=$PWD/config/mapper_params_online_async.yaml` | Pi |
| Start Octomap | `ros2 launch r2_bringup octomap.launch.py` | Pi |
| Control robot | `ros2 run teleop_twist_keyboard teleop_twist_keyboard` | Pi or Laptop |
| Visualize | `rviz2` | Laptop |
| Save 2D map | `ros2 run nav2_map_server map_saver_cli -f map_name` | Pi |
| Save 3D map | `ros2 service call /octomap_server/save_map ...` | Pi |
| View topics | `ros2 topic list` | Pi or Laptop |
| Check TF | `ros2 run tf2_tools view_frames` | Pi |
| Monitor rate | `ros2 topic hz /topic_name` | Pi or Laptop |
