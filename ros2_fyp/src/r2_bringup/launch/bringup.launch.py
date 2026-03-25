from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    # Launch args (so you can override at runtime if needed)
    rplidar_port = LaunchConfiguration('rplidar_port')
    rplidar_baud = LaunchConfiguration('rplidar_baud')
    use_teleop = LaunchConfiguration('use_teleop')

    declare_rplidar_port = DeclareLaunchArgument(
        'rplidar_port',
        default_value='/dev/rplidar',
        description='Serial port for RPLidar'
    )

    declare_rplidar_baud = DeclareLaunchArgument(
        'rplidar_baud',
        default_value='115200',
        description='Baudrate for RPLidar'
    )

    declare_use_teleop = DeclareLaunchArgument(
        'use_teleop',
        default_value='false',
        description='Start teleop_twist_keyboard (interactive; usually run in its own terminal)'
    )

    # --- Include: r2_description ---
    r2_description_share = get_package_share_directory('r2_description')
    r2_description_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(r2_description_share, 'launch', 'description.launch.py')
        )
    )

    # --- Include: rplidar_ros (your ros2 launch ... serial_port:= ... serial_baudrate:= ...) ---
    rplidar_share = get_package_share_directory('rplidar_ros')
    rplidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(rplidar_share, 'launch', 'rplidar_a1_launch.py')
        ),
        launch_arguments={
            'serial_port': rplidar_port,
            'serial_baudrate': rplidar_baud,
        }.items()
    )

    # --- Include: r2_driver launch ---
    r2_driver_share = get_package_share_directory('r2_driver')
    r2_driver_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(r2_driver_share, 'launch', 'r2_driver.launch.py')
        )
    )

    # --- Include: Astra camera ---
    astra_camera_share = get_package_share_directory('astra_camera')
    astra_camera_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(astra_camera_share, 'launch', 'astra_mini.launch.py')
        )
    )

    # --- Node: r2_wheel_odometry ---
    wheel_odom_node = Node(
        package='r2_wheel_odometry',
        executable='wheel_odom',
        name='wheel_odom',
        output='screen',
    )

    return LaunchDescription([
        declare_rplidar_port,
        declare_rplidar_baud,
        declare_use_teleop,

        r2_description_launch,
        rplidar_launch,
        r2_driver_launch,
        astra_camera_launch,
        wheel_odom_node,

        # teleop_node,  # uncomment if you really want teleop inside this launch
    ])
