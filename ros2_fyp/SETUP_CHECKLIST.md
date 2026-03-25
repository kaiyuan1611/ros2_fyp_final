# 3D Mapping Setup Checklist

## Pre-Flight Checklist

### 1. Software Installation

**On Raspberry Pi:**
- [ ] Install Octomap packages:
  ```bash
  sudo apt update
  sudo apt install ros-humble-octomap-server ros-humble-octomap-msgs
  ```

- [ ] Verify workspace is built:
  ```bash
  cd ~/ros2_fyp
  colcon build
  source install/setup.bash
  ```

**On Laptop (for visualization):**
- [ ] Install ROS2 Humble (if not already)
- [ ] Install RViz and plugins:
  ```bash
  sudo apt install ros-humble-rviz2 ros-humble-octomap-rviz-plugins
  ```

- [ ] Set ROS_DOMAIN_ID to match Pi:
  ```bash
  export ROS_DOMAIN_ID=0  # Add to ~/.bashrc
  ```

### 2. Hardware Setup (on Raspberry Pi)
- [ ] RPLidar A1 connected to `/dev/rplidar`
- [ ] Astra camera connected via USB
- [ ] Verify camera detection:
  ```bash
  lsusb | grep -i orbbec
  # Should show: Orbbec 3D Technology Co., Ltd.
  ```

### 3. Network Setup
- [ ] Pi and laptop on same network
- [ ] Can ping Pi from laptop: `ping <pi_ip>`
- [ ] ROS_DOMAIN_ID matches on both machines
- [ ] Test topic visibility from laptop:
  ```bash
  # On laptop
  export ROS_DOMAIN_ID=0
  source /opt/ros/humble/setup.bash
  ros2 topic list  # Should see topics from Pi
  ```

### 4. Camera Mounting Position
- [ ] Measure camera position relative to robot center (base_link)
  - Forward distance (X): _____ meters
  - Left distance (Y): _____ meters  
  - Height (Z): _____ meters
  - Rotation (if any): _____ degrees

- [ ] Update URDF with measured values:
  ```bash
  nano ~/ros2_fyp/src/r2_description/urdf/r2.urdf.xacro
  # Edit line ~27: <origin xyz="X Y Z" rpy="0 0 0"/>
  ```

- [ ] Rebuild after URDF changes:
  ```bash
  cd ~/ros2_fyp
  colcon build --packages-select r2_description
  source install/setup.bash
  ```

### 5. First Test - Individual Components (All on Raspberry Pi)

#### Test 1: Base Robot
```bash
ros2 launch r2_bringup bringup.launch.py
```
- [ ] No errors in terminal
- [ ] Can see `/scan` topic: `ros2 topic list | grep scan`
- [ ] Can see `/odom` topic: `ros2 topic list | grep odom`

#### Test 2: Astra Camera (in new terminal)
```bash
source ~/ros2_fyp/install/setup.bash
ros2 launch r2_bringup astra_camera.launch.py
```
- [ ] Camera initializes without errors
- [ ] Can see depth image: `ros2 topic list | grep depth/image`
- [ ] Can see point cloud: `ros2 topic list | grep depth/points`
- [ ] Verify point cloud data:
  ```bash
  ros2 topic echo /camera/depth/points --no-arr
  # Should show point cloud data
  ```

#### Test 3: SLAM Toolbox (in new terminal)
```bash
source ~/ros2_fyp/install/setup.bash
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=~/ros2_fyp/config/mapper_params_online_async.yaml
```
- [ ] SLAM initializes
- [ ] Can see `/map` topic
- [ ] Drive robot a bit, map should update

#### Test 4: Octomap (in new terminal)
```bash
source ~/ros2_fyp/install/setup.bash
ros2 launch r2_bringup octomap.launch.py
```
- [ ] Octomap starts without errors
- [ ] Can see `/octomap_binary` topic
- [ ] Can see `/occupied_cells_vis_array` topic

### 6. Full System Test (All on Raspberry Pi)

#### Launch all components in separate terminals (or use tmux):

**Terminal 1:**
```bash
cd ~/ros2_fyp
source install/setup.bash
ros2 launch r2_bringup bringup.launch.py
```

**Terminal 2:**
```bash
cd ~/ros2_fyp
source install/setup.bash
ros2 launch r2_bringup astra_camera.launch.py
```

**Terminal 3:**
```bash
cd ~/ros2_fyp
source install/setup.bash
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=$PWD/config/mapper_params_online_async.yaml
```

**Terminal 4:**
```bash
cd ~/ros2_fyp
source install/setup.bash
ros2 launch r2_bringup octomap.launch.py
```

- [ ] All nodes start successfully
- [ ] No TF errors (may see warnings initially, should resolve)
- [ ] All expected topics present:
  ```bash
  ros2 topic list
  # Should include: /scan, /map, /camera/depth/points, /octomap_binary
  ```

### 7. Visualization Test (On Laptop)

### 7. Visualization Test (On Laptop)

**On your laptop:**

```bash
# Set ROS_DOMAIN_ID to match Pi
export ROS_DOMAIN_ID=0

# Source ROS2
source /opt/ros/humble/setup.bash

# Launch RViz
rviz2
```

Or copy and use the pre-configured setup:
```bash
# One-time: Copy config from Pi
scp pi@<pi_ip>:~/ros2_fyp/config/3d_mapping.rviz ~/

# Launch with config
rviz2 -d ~/3d_mapping.rviz
```

**In RViz, verify:**
- [ ] Robot model appears
- [ ] TF frames visible (map, odom, base_link, laser, camera_link)
- [ ] Red laser scan visible
- [ ] 2D map building (gray/black/white grid)
- [ ] Point cloud visible (colored depth data)
- [ ] 3D occupancy cubes appearing (may take a moment)

### 8. Mapping Test

#### Control the robot (on Pi or laptop):
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

**Drive the robot and verify:**
- [ ] 2D map updates as you move
- [ ] 3D occupancy grid builds up
- [ ] Point cloud moves with robot
- [ ] No major TF errors or warnings

### 9. Save Test Maps (On Raspberry Pi)

#### Save 2D map:
```bash
cd ~/ros2_fyp
ros2 run nav2_map_server map_saver_cli -f test_2d_map
```
- [ ] Creates `test_2d_map.pgm` and `test_2d_map.yaml`

#### Save 3D map:
```bash
ros2 service call /octomap_server/save_map \
  octomap_msgs/srv/SaveMap "{filename: 'test_3d_map.ot'}"
```
- [ ] Creates `test_3d_map.ot`
- [ ] File size > 0 bytes

## Troubleshooting

### Issue: "No transform from camera_depth_optical_frame to map"
**Solution:**
1. Wait 5-10 seconds for SLAM to initialize
2. Drive robot forward/backward to build initial map
3. Check TF tree: `ros2 run tf2_tools view_frames`

### Issue: Point cloud not visible in RViz
**Solution:**
1. Check topic: `ros2 topic hz /camera/depth/points`
2. Verify camera connection: `lsusb | grep Orbbec`
3. Check camera launch: `ros2 node list | grep camera`
4. Try restarting camera node

### Issue: Octomap is empty
**Solution:**
1. Verify SLAM is running: `ros2 topic hz /map`
2. Check TF: `ros2 run tf2_tools view_frames`
3. Verify point cloud has data: `ros2 topic echo /camera/depth/points --no-arr`
4. Drive robot to generate map data

### Issue: High CPU usage
**Solution:**
1. Increase Octomap resolution: Change `0.05` to `0.1` in `octomap.launch.py`
2. Reduce camera resolution in Astra params
3. Limit max range in Octomap config

### Issue: Camera position looks wrong in RViz
**Solution:**
1. Re-measure camera mounting position
2. Update URDF: `src/r2_description/urdf/r2.urdf.xacro`
3. Rebuild: `colcon build --packages-select r2_description`
4. Restart launch file

### Issue: RViz on laptop not showing data
**Solution:**
1. Verify network connectivity: `ping <pi_ip>`
2. Check ROS_DOMAIN_ID matches: `echo $ROS_DOMAIN_ID` (on both machines)
3. Test topic visibility: `ros2 topic list` (on laptop)
4. Check firewall settings (ROS2 uses UDP multicast)
5. Ensure both machines on same subnet

### Issue: Managing multiple SSH terminals
**Solution:**
Use `tmux` for easier terminal management:
```bash
# On Pi, install tmux
sudo apt install tmux

# Start session
tmux new -s mapping

# Split panes: Ctrl+b then " (horizontal) or % (vertical)
# Switch panes: Ctrl+b then arrow keys
# Detach: Ctrl+b then d
# Reattach: tmux attach -t mapping
```

## Performance Expectations

**Normal Operation:**
- CPU: 30-50% on quad-core processor
- Memory: 300-500 MB
- Map update rate: 1-5 Hz
- Point cloud rate: 10-30 Hz
- Laser scan rate: 5-10 Hz

**If performance is poor:**
- Reduce Octomap resolution
- Lower camera frame rate
- Reduce max range
- Close unnecessary applications

## Success Criteria

✓ All nodes launch without errors
✓ Robot localizes in map frame
✓ 2D map builds from laser data
✓ 3D occupancy grid builds from depth data
✓ Can save both 2D and 3D maps
✓ Visualization works in RViz
✓ Can control robot and map environment

## Next Steps After Successful Setup

1. Map your actual environment
2. Tune Octomap parameters for your use case
3. Add point cloud filtering for cleaner maps
4. Integrate with Nav2 for autonomous navigation
5. Experiment with different resolutions and ranges

---

**Setup Date**: _______________
**Tested By**: _______________
**Status**: [ ] Complete [ ] In Progress [ ] Issues

**Notes:**
_____________________________________________
_____________________________________________
_____________________________________________
