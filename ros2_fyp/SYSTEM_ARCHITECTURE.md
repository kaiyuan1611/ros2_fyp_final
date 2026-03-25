# System Architecture - 3D Mapping with SLAM Toolbox + Octomap

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         ROBOT HARDWARE                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ RPLidar A1   │  │ Astra Camera │  │ Wheel Motors │         │
│  │ (2D Laser)   │  │ (RGB-D)      │  │ + Encoders   │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
└─────────┼──────────────────┼──────────────────┼────────────────┘
          │                  │                  │
          │ /scan            │ depth/RGB        │ encoder ticks
          ↓                  ↓                  ↓
┌─────────────────────────────────────────────────────────────────┐
│                      ROS2 MIDDLEWARE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐  │
│  │ rplidar_node   │  │ astra_camera   │  │ wheel_odom      │  │
│  │                │  │                │  │                 │  │
│  │ Publishes:     │  │ Publishes:     │  │ Publishes:      │  │
│  │ • /scan        │  │ • /camera/     │  │ • /odom         │  │
│  │                │  │   depth/points │  │                 │  │
│  └────────┬───────┘  └────────┬───────┘  └────────┬────────┘  │
│           │                   │                    │           │
│           │                   │                    │           │
│           ↓                   │                    ↓           │
│  ┌─────────────────────────────┐         ┌─────────────────┐  │
│  │    SLAM Toolbox             │         │ robot_state_    │  │
│  │    (2D SLAM)                │←────────│ publisher       │  │
│  │                             │         │                 │  │
│  │ Subscribes: /scan, /odom    │         │ Publishes TF:   │  │
│  │ Publishes:                  │         │ • base_footprint│  │
│  │ • /map (2D occupancy)       │         │ • base_link     │  │
│  │ • TF: map→odom              │         │ • laser         │  │
│  │                             │         │ • camera_link   │  │
│  └──────────┬──────────────────┘         └─────────────────┘  │
│             │                                                  │
│             │ TF: map→odom→base_link                          │
│             │                                                  │
│             ↓                            ↑                     │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │              Octomap Server                             │  │
│  │              (3D Mapping)                               │  │
│  │                                                         │  │
│  │ Subscribes:                                            │  │
│  │ • /camera/depth/points (point cloud)                   │  │
│  │ • TF tree (for positioning)                            │  │
│  │                                                         │  │
│  │ Publishes:                                             │  │
│  │ • /octomap_binary (3D occupancy grid)                  │  │
│  │ • /occupied_cells_vis_array (visualization)            │  │
│  │ • /projected_map (2D projection)                       │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## TF (Transform) Tree

```
map (world frame - fixed)
 │
 └─→ odom (odometry frame - drifts over time)
      │
      └─→ base_footprint (ground projection of robot)
           │
           └─→ base_link (robot center)
                │
                ├─→ laser (RPLidar sensor frame)
                │    └─ Publishes: /scan
                │
                └─→ camera_link (Astra camera mounting point)
                     │
                     └─→ camera_depth_optical_frame (optical frame)
                          └─ Publishes: /camera/depth/points

Legend:
→ : Fixed transform (from URDF)
map→odom : Published by SLAM Toolbox (corrects drift)
```

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                    LOCALIZATION PIPELINE                         │
└──────────────────────────────────────────────────────────────────┘

Wheel Encoders → wheel_odom → /odom (odometry estimate)
                                  ↓
RPLidar A1 → /scan ──────────→ SLAM Toolbox
                                  │
                                  ├─→ /map (2D occupancy grid)
                                  │
                                  └─→ TF: map→odom (drift correction)


┌──────────────────────────────────────────────────────────────────┐
│                    3D MAPPING PIPELINE                           │
└──────────────────────────────────────────────────────────────────┘

Astra Camera → depth image → point_cloud_xyz → /camera/depth/points
                                                        ↓
                                                   Octomap Server
                                                   (uses TF from SLAM)
                                                        ↓
                                                   /octomap_binary
                                                   (3D occupancy grid)
```

## Node Communication Graph

```
┌─────────────┐     /scan      ┌──────────────┐
│rplidar_node │───────────────→│ slam_toolbox │
└─────────────┘                 └──────┬───────┘
                                       │
┌─────────────┐     /odom             │ /map
│ wheel_odom  │───────────────────────┤
└─────────────┘                       │
                                      ↓
┌──────────────┐  /camera/depth/  ┌──────────────┐
│astra_camera  │─────points──────→│octomap_server│
└──────────────┘                  └──────┬───────┘
                                         │
                                         │ /octomap_binary
                                         │ /occupied_cells_vis_array
                                         ↓
                                    [Visualization]
                                    [Navigation]
                                    [Planning]
```

## Launch File Hierarchy

Modular launch approach for flexibility:

```
bringup.launch.py (base robot)
├─→ description.launch.py (robot URDF + robot_state_publisher)
├─→ wheel_odom node
├─→ rplidar_a1_launch.py
└─→ r2_driver.launch.py

astra_camera.launch.py (separate)
└─→ astra_camera nodes (driver + point cloud generation)

online_async_launch.py (SLAM Toolbox - separate)
└─→ async_slam_toolbox_node

octomap.launch.py (separate)
└─→ octomap_server_node

Each component launches independently for maximum flexibility.
Useful when SSH-ing into robot - can start/stop components as needed.
```

## Topic Reference

### Input Topics (Sensors)
| Topic | Type | Rate | Source | Description |
|-------|------|------|--------|-------------|
| `/scan` | sensor_msgs/LaserScan | 5-10 Hz | RPLidar | 2D laser scan |
| `/odom` | nav_msgs/Odometry | 20-50 Hz | wheel_odom | Wheel odometry |
| `/camera/depth/image_raw` | sensor_msgs/Image | 30 Hz | Astra | Depth image |
| `/camera/color/image_raw` | sensor_msgs/Image | 30 Hz | Astra | RGB image |
| `/camera/depth/points` | sensor_msgs/PointCloud2 | 10-30 Hz | Astra | 3D point cloud |

### Output Topics (Maps)
| Topic | Type | Rate | Source | Description |
|-------|------|------|--------|-------------|
| `/map` | nav_msgs/OccupancyGrid | 0.2 Hz | SLAM Toolbox | 2D occupancy grid |
| `/octomap_binary` | octomap_msgs/Octomap | 1-5 Hz | Octomap | 3D occupancy grid (binary) |
| `/octomap_full` | octomap_msgs/Octomap | 1-5 Hz | Octomap | 3D occupancy grid (full) |
| `/occupied_cells_vis_array` | visualization_msgs/MarkerArray | 1-5 Hz | Octomap | 3D visualization |
| `/projected_map` | nav_msgs/OccupancyGrid | 1-5 Hz | Octomap | 2D projection of 3D map |

### TF Frames
| Frame | Parent | Published By | Description |
|-------|--------|--------------|-------------|
| `map` | - | SLAM Toolbox | World frame (fixed) |
| `odom` | `map` | SLAM Toolbox | Odometry frame (drift-corrected) |
| `base_footprint` | `odom` | wheel_odom | Ground projection |
| `base_link` | `base_footprint` | robot_state_publisher | Robot center |
| `laser` | `base_link` | robot_state_publisher | RPLidar frame |
| `camera_link` | `base_link` | robot_state_publisher | Camera mounting |
| `camera_depth_optical_frame` | `camera_link` | robot_state_publisher | Optical frame |

## Processing Pipeline

### 2D SLAM (SLAM Toolbox)
```
1. Receive /scan from RPLidar
2. Receive /odom from wheel encoders
3. Perform scan matching
4. Update 2D occupancy grid (/map)
5. Publish corrected TF: map→odom
6. Detect loop closures
7. Optimize pose graph
```

### 3D Mapping (Octomap)
```
1. Receive /camera/depth/points
2. Lookup TF: map→camera_depth_optical_frame
3. Transform points to map frame
4. Insert points into octree structure
5. Update occupancy probabilities
6. Publish /octomap_binary
7. Generate visualization markers
8. Project to 2D for /projected_map
```

## Memory and Performance

### Typical Resource Usage
- **CPU**: 30-50% (quad-core)
- **Memory**: 300-500 MB
- **Disk** (for saved maps):
  - 2D map: ~1-5 MB (PGM + YAML)
  - 3D map: ~10-100 MB (depends on environment size and resolution)

### Performance Tuning Parameters

**Octomap Resolution:**
- `0.02` - Very detailed (2cm voxels) - High CPU/memory
- `0.05` - Balanced (5cm voxels) - Recommended
- `0.10` - Fast (10cm voxels) - Low CPU/memory

**Point Cloud Processing:**
- Reduce camera FPS (30→15 Hz)
- Downsample point cloud
- Limit max range (5.0→3.0 m)

## Coordinate Frame Conventions

### ROS Standard (REP 103)
- **X**: Forward
- **Y**: Left
- **Z**: Up

### Camera Optical Frame (REP 103)
- **X**: Right
- **Y**: Down
- **Z**: Forward (into scene)

### Rotation from camera_link to optical frame
```
rpy = [-π/2, 0, -π/2]
```
This aligns camera coordinate system with ROS conventions.

## Integration Points

### For Navigation (Nav2)
- Subscribe to `/map` for 2D costmap
- Subscribe to `/projected_map` for 3D obstacle projection
- Use `/octomap_binary` for 3D collision checking

### For Manipulation
- Use `/camera/depth/points` for object detection
- Query `/octomap_binary` for workspace occupancy
- Transform objects to `base_link` frame

### For Autonomous Exploration
- Use `/map` to identify frontiers
- Use `/octomap_binary` to verify 3D traversability
- Combine 2D and 3D data for safe path planning

---

**Architecture Version**: 1.0
**Last Updated**: December 2025
**ROS2 Distribution**: Humble
