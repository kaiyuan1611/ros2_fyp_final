from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('voxel_size', default_value='0.03',
                             description='Voxel downsample size in meters'),
        DeclareLaunchArgument('max_points', default_value='500000',
                             description='Max accumulated points'),
        DeclareLaunchArgument('max_range', default_value='4.0',
                             description='Max depth range in meters'),

        Node(
            package='r2_cloud_accumulator',
            executable='cloud_accumulator',
            name='cloud_accumulator',
            output='screen',
            parameters=[{
                'input_topic': '/camera/depth/points',
                'output_topic': '/accumulated_cloud',
                'map_frame': 'map',
                'voxel_size': LaunchConfiguration('voxel_size'),
                'max_points': LaunchConfiguration('max_points'),
                'max_range': LaunchConfiguration('max_range'),
                'min_range': 0.3,
            }],
        ),
    ])
