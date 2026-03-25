# 3D Mapping Implementation Summary

## What Was Implemented

### Architecture: SLAM Toolbox + Octomap
- **SLAM Toolbox**: Handles 2D SLAM using RPLidar A1 (localization + 2D mapping)
- **Octomap**: Builds 3D occupancy grid using Astra camera depth data
- **Integration**: Octomap uses the robot pose from SLAM Toolbox to position 3D points

### Why This Approach?
✓ Lower computational cost than full 3D SLAM
✓ Leverages your existing 2D SLAM setup
✓ Robust localization from laser scanner
✓ Rich 3D environmental representation from depth camera
✓ Both sensors complement each other

## Files Created/Modified

### Modified Files
1. **src/r2_description/urdf/r2.urdf.xacro**
   - Added camera_link frame
   - Added camera_depth_optical_frame (ROS optical convention)
   - Positioned camera relative to base_link

### New Launch Files
1. **src/r2_bringup/launch/astra_camera.launch.py**
   - Launches Astra camera driver
   - Generates point cloud from depth data
   - Disables camera's internal TF (uses robot_state_publisher instead)

2. **src/r2_bringup/launch/octomap.launch.py**
   - Launches Octomap server
   - Configured for Astra camera range (0.3m - 5.0m)
   - Subscribes to /camera/depth/points
   - Publishes 3D occupancy grid

Note: Modular design allows launching components separately for flexibility, especially useful when SSH-ing into the robot.

### Configuration Files
1. **config/3d_mapping.rviz**
   - Pre-configured RViz layout
   - Shows: robot, TF, laser, 2D map, point cloud, 3D map

### Documentation
1. **3D_MAPPING_SETUP.md** - Detailed setup and configuration guide
2. **QUICK_START.md** - Quick reference for daily use
3. **IMPLEMENTATION_SUMMARY.md** - This file

## Data Flow

```
┌─────────────┐
│  RPLidar A1 │──> /scan
└─────────────┘         │
                        ↓
                 ┌──────────────┐
                 │ SLAM Toolbox │──> /map (2D)
                 └──────────────┘
                        │
                        ↓
                   TF: map->odom->base_link
                        ↑
                        │ (uses for positioning)
┌──────────────┐       │
│ Astra Camera │──> /camera/depth/points
└──────────────┘       │
                       ↓
                 ┌──────────┐
                 │ Octomap  │──> /octomap_binary (3D)
                 └──────────┘──> /occupied_cells_vis_array
                              └─> /projected_map (2D projection)
```

## Key Topics

### Inputs
- `/scan` - 2D laser scan from RPLidar
- `/camera/depth/points` - 3D point cloud from Astra
- `/odom` - Wheel odometry

### Outputs
- `/map` - 2D occupancy grid (SLAM Toolbox)
- `/octomap_binary` - 3D occupancy grid (Octomap)
- `/occupied_cells_vis_array` - 3D visualization markers
- `/projected_map` - 2D projection of 3D map

## TF Tree

```
map
 └─ odom
     └─ base_footprint
         └─ base_link
             ├─ laser (RPLidar)
             └─ camera_link
                 └─ camera_depth_optical_frame (Astra)
```

## Installation Requirements

```bash
# On Raspberry Pi
sudo apt install ros-humble-octomap-server \
                 ros-humble-octomap-msgs

# On Laptop (for visualization)
sudo apt install ros-humble-rviz2 \
                 ros-humble-octomap-rviz-plugins

# Already in workspace:
# - astra_camera
# - slam_toolbox
# - rplidar_ros
```

## Usage Commands

### Start Components (On Raspberry Pi - Separate Terminals)

**Terminal 1: Base System**
```bash
cd ~/ros2_fyp
source install/setup.bash
ros2 launch r2_bringup bringup.launch.py
```

**Terminal 2: Camera**
```bash
cd ~/ros2_fyp
source install/setup.bash
ros2 launch r2_bringup astra_camera.launch.py
```

**Terminal 3: SLAM**
```bash
cd ~/ros2_fyp
source install/setup.bash
ros2 launch slam_toolbox online_async_launch.py \
  slam_params_file:=$PWD/config/mapper_params_online_async.yaml
```

**Terminal 4: Octomap**
```bash
cd ~/ros2_fyp
source install/setup.bash
ros2 launch r2_bringup octomap.launch.py
```

### Visualization (On Laptop)
```bash
export ROS_DOMAIN_ID=0  # Match Pi's domain ID
source /opt/ros/humble/setup.bash
rviz2
```

### Save Maps (On Raspberry Pi)
```bash
# 2D map
cd ~/ros2_fyp
ros2 run nav2_map_server map_saver_cli -f my_2d_map

# 3D map
ros2 service call /octomap_server/save_map \
  octomap_msgs/srv/SaveMap "{filename: 'my_3d_map.ot'}"

# Copy to laptop
# On laptop:
scp pi@<pi_ip>:~/ros2_fyp/my_2d_map.* ~/maps/
scp pi@<pi_ip>:~/ros2_fyp/my_3d_map.ot ~/maps/
```

## Configuration Parameters

### Octomap (in octomap.launch.py)
- `resolution: 0.05` - Voxel size (5cm cubes)
- `sensor_model.max_range: 5.0` - Max depth range
- `sensor_model.min_range: 0.3` - Min depth range
- `filter_ground: False` - Ground plane filtering

### Camera Position (in r2.urdf.xacro)
```xml
<origin xyz="0.10 0.00 0.15" rpy="0 0 0"/>
```
**IMPORTANT**: Adjust based on actual mounting position!

## Next Steps

### Immediate
1. ✓ Install Octomap on Pi: `sudo apt install ros-humble-octomap-server ...`
2. ✓ Install RViz on laptop: `sudo apt install ros-humble-rviz2 ...`
3. ✓ Build workspace: `colcon build`
4. Set ROS_DOMAIN_ID on both machines
5. Measure and update camera position in URDF
6. Test: Launch components in separate terminals

### Short Term
1. Tune Octomap parameters for your environment
2. Add point cloud filtering (remove noise, outliers)
3. Calibrate camera intrinsics if needed
4. Test in different environments

### Long Term
1. Integrate with Nav2 for 3D obstacle avoidance
2. Add semantic segmentation (identify objects)
3. Implement map merging for multi-robot systems
4. Add dynamic object filtering

## Advantages of This Setup

1. **Computational Efficiency**: 2D SLAM is less intensive than 3D SLAM
2. **Robust Localization**: Laser scanner provides reliable odometry
3. **Rich 3D Data**: Depth camera adds environmental detail
4. **Modular**: Can run components independently for testing and flexibility
5. **SSH-Friendly**: Components run on Pi, visualization on laptop
6. **Scalable**: Easy to add more sensors or processing nodes
7. **Standard ROS2**: Uses well-maintained, community-supported packages

## Comparison with Alternatives

| Feature | This Setup | RTAB-Map | Cartographer 3D |
|---------|-----------|----------|-----------------|
| Computational Cost | Low | Medium | High |
| 3D Map Quality | Good | Excellent | Excellent |
| Setup Complexity | Simple | Medium | Complex |
| Sensor Fusion | Yes | Yes | Yes |
| Loop Closure | 2D only | 3D | 3D |
| Best For | Resource-constrained | Feature-rich 3D | Research/High-end |

## Troubleshooting Reference

### Common Issues
1. **No TF transform**: Wait for SLAM to initialize, drive robot
2. **Empty Octomap**: Check SLAM is running, verify TF tree
3. **No point cloud**: Check camera connection, verify topics
4. **Wrong camera position**: Update URDF and rebuild

### Diagnostic Commands
```bash
# Check topics
ros2 topic list

# Check TF tree
ros2 run tf2_tools view_frames

# Monitor point cloud
ros2 topic echo /camera/depth/points --no-arr

# Check Octomap status
ros2 topic hz /octomap_binary
```

## Performance Benchmarks (Typical)

- **CPU Usage**: 30-50% on modern quad-core
- **Memory**: ~500MB for moderate-sized maps
- **Map Update Rate**: 1-5 Hz (depends on resolution)
- **Mapping Range**: 0.3m - 5.0m (Astra camera limits)

## Support and Resources

- Octomap: https://octomap.github.io/
- SLAM Toolbox: https://github.com/SteveMacenski/slam_toolbox
- Astra Camera: https://github.com/orbbec/ros2_astra_camera
- ROS2 Navigation: https://navigation.ros.org/

---

**Implementation Date**: December 2025
**ROS2 Distribution**: Humble
**Status**: Ready for testing
