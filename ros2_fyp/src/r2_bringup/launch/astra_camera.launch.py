from launch import LaunchDescription
from launch_ros.actions import Node, ComposableNodeContainer
from launch_ros.descriptions import ComposableNode
from ament_index_python import get_package_share_directory
import yaml


def generate_launch_description():
    # Load Astra camera parameters
    params_file = get_package_share_directory("astra_camera") + "/params/astra_mini_params.yaml"
    
    with open(params_file, 'r') as file:
        config_params = yaml.safe_load(file)
    
    # Override some parameters for your robot
    config_params['camera_name'] = 'camera'
    config_params['publish_tf'] = False  # We'll publish TF from robot_state_publisher
    
    # Astra camera container with point cloud generation
    camera_container = ComposableNodeContainer(
        name='astra_camera_container',
        namespace='',
        package='rclcpp_components',
        executable='component_container',
        composable_node_descriptions=[
            ComposableNode(
                package='astra_camera',
                plugin='astra_camera::OBCameraNodeFactory',
                name='camera',
                namespace='camera',
                parameters=[config_params]
            ),
            ComposableNode(
                package='astra_camera',
                plugin='astra_camera::PointCloudXyzNode',
                namespace='camera',
                name='point_cloud_xyz'
            ),
        ],
        output='screen'
    )
    
    return LaunchDescription([camera_container])
