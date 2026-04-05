from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    # Launch arguments
    resolution = LaunchConfiguration('resolution')
    frame_id = LaunchConfiguration('frame_id')
    
    declare_resolution = DeclareLaunchArgument(
        'resolution',
        default_value='0.01',
        description='Octomap resolution in meters (smaller = more detailed but more memory)'
    )
    
    declare_frame_id = DeclareLaunchArgument(
        'frame_id',
        default_value='map',
        description='Frame ID for the octomap'
    )
    
    # Octomap server node with advanced filtering
    octomap_server = Node(
        package='octomap_server',
        executable='octomap_server_node',
        name='octomap_server',
        output='screen',
        parameters=[{
            'resolution': resolution,
            'frame_id': frame_id,
            'sensor_model.max_range': 3.0,  # Reduced from 5.0
            'sensor_model.min_range': 0.4,  # Increased from 0.3 
            'latch': True,
            
            # Ground filtering
            'filter_ground': True,
            'ground_filter/distance': 0.04,
            'ground_filter/angle': 0.15,
            'ground_filter/plane_distance': 0.07,
            
            # Height filtering
            'occupancy_min_z': -0.1,  # Just below floor level
            'occupancy_max_z': 0.8,   # Just below ceiling
            'pointcloud_min_z': -0.1,
            'pointcloud_max_z': 0.8,
            
            # Map compression and projection
            'compress_map': True,
            'incremental_2D_projection': True,
            
            # Advanced filtering to reduce motion artifacts
            'filter_speckles': True,        # Remove isolated voxels
            'max_octree_depth': 16,         # Limit tree depth for performance
            
            # Probabilistic parameters 
            'sensor_model.hit': 0.85,        # Probability for occupied (default 0.7)
            'sensor_model.miss': 0.3,       # Probability for free (default 0.4)
            'sensor_model.min': 0.12,       # Min probability (default 0.12)
            'sensor_model.max': 0.97,       # Max probability (default 0.97)
            
            # Update frequency (reduce to avoid processing during fast motion)
            'map_update_interval': 1.0,    
        
        }],
        remappings=[
            ('cloud_in', '/camera/depth/points'),  # Subscribe to Astra point cloud
        ]
    )
    
    return LaunchDescription([
        declare_resolution,
        declare_frame_id,
        octomap_server,
    ])
