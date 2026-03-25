"""
RTAB-Map 3D mapping launch for R2 robot.

Uses: Depth point cloud + RPLidar 2D scan + Wheel odometry.
No RGB/IR image needed - uses scan_cloud for 3D and scan for loop closure.
QoS set to best_effort to match Astra camera publishers.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')

    rtabmap_params = {
        'use_sim_time': use_sim_time,

        # Subscriptions - point cloud + 2D scan only (no RGB needed)
        'subscribe_depth': False,
        'subscribe_rgb': False,
        'subscribe_scan': True,             # RPLidar 2D scan for loop closure
        'subscribe_scan_cloud': True,       # Astra depth point cloud for 3D map
        'subscribe_stereo': False,
        'subscribe_odom_info': False,

        # Frames
        'frame_id': 'base_link',
        'odom_frame_id': 'odom',
        'map_frame_id': 'map',
        'publish_tf': True,
        'wait_for_transform': 0.3,

        # QoS
        'qos_scan': 0,
        'qos_odom': 0,

        # Core RTAB-Map
        'Rtabmap/DetectionRate': '1.0',
        'Rtabmap/CreateIntermediateNodes': 'true',
        'Rtabmap/ImageBufferSize': '1',

        # RGBD SLAM enabled
        'RGBD/Enabled': 'true',
        'RGBD/AngularUpdate': '0.1',
        'RGBD/LinearUpdate': '0.1',
        'RGBD/OptimizeFromGraphEnd': 'false',

        # No visual features (no image input)
        'Kp/MaxFeatures': '-1',

        # Loop closure via ICP scan matching
        'Reg/Strategy': '1',               # 1 = ICP
        'Reg/Force3DoF': 'true',            # 2D robot

        # ICP parameters
        'Icp/VoxelSize': '0.05',
        'Icp/MaxCorrespondenceDistance': '0.15',
        'Icp/MaxIterations': '30',
        'Icp/CorrespondenceRatio': '0.1',
        'Icp/PointToPlane': 'false',        # 2D scan, use point-to-point

        # Graph optimization
        'Optimizer/Strategy': '1',          # g2o
        'Optimizer/Iterations': '100',

        # Grid / 3D map - built from the scan_cloud (Astra point cloud)
        'Grid/Sensor': '1',                # 0=scan, 1=depth/cloud - use 3D cloud
        'Grid/FromDepth': 'true',           # Build grid from 3D cloud data
        'Grid/CellSize': '0.05',
        'Grid/RangeMax': '4.0',
        'Grid/RangeMin': '0.4',
        'Grid/MaxObstacleHeight': '2.0',
        'Grid/MaxGroundHeight': '0.1',
        'Grid/NormalsSegmentation': 'true', # Separate ground from obstacles using normals
        'Grid/3D': 'true',
        'Grid/GroundIsObstacle': 'false',
        'Grid/NoiseFilteringRadius': '0.05',
        'Grid/NoiseFilteringMinNeighbors': '5',

        # Memory
        'Mem/RehearsalSimilarity': '0.30',
        'Mem/IncrementalMemory': 'true',
    }

    rtabmap_node = Node(
        package='rtabmap_slam',
        executable='rtabmap',
        name='rtabmap',
        output='screen',
        parameters=[rtabmap_params],
        arguments=['--delete_db_on_start'],
        remappings=[
            ('scan_cloud', '/camera/depth/points'),
            ('scan', '/scan'),
            ('odom', '/odom'),
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        rtabmap_node,
    ])
