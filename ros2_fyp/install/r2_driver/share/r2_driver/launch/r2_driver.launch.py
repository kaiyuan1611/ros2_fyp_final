from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='r2_driver',
            executable='r2_driver_node',
            name='r2_driver',
            output='screen',
            parameters=[
                {'max_speed': 1.0},
                {'max_steer_angle_deg': 30.0},
                {'servo_id': 1},
                {'center_angle_deg': 90.0},
                {'min_angle_deg': 60.0},
                {'max_angle_deg': 120.0},
                {'cmd_vel_timeout': 0.5},
                {'control_rate_hz': 20.0},
            ]
        )
    ])
