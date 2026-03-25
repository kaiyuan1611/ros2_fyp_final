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
        default_value='0.02',
        description='Octomap resolution in meters (smaller = more detailed but more memory)'
    )
    
    declare_frame_id = DeclareLaunchArgument(
        'frame_id',
        default_value='map',
        description='Frame ID for the octomap'
    )
    
    # Octomap server node
    octomap_server = Node(
        package='octomap_server',
        executable='octomap_server_node',
        name='octomap_server',
        output='screen',
        parameters=[{
            'resolution': resolution,
            'frame_id': frame_id,
            'sensor_model.max_range': 5.0,  # Max range for Astra camera (meters)
            'sensor_model.min_range': 0.3,  # Min range for Astra camera (meters)
            'latch': True,
            'filter_ground': False,  # Set to True if you want to filter ground plane
            'ground_filter/distance': 0.04,
            'ground_filter/angle': 0.15,
            'ground_filter/plane_distance': 0.07,
            'compress_map': True,
            'incremental_2D_projection': True,  # For 2D costmap compatibility
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
