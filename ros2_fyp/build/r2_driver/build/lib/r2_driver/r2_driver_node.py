#!/usr/bin/env python3

import math
from std_msgs.msg import Float32

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

from Rosmaster_Lib import Rosmaster


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


class R2DriverNode(Node):
    """
    ROS2 driver for Yahboom Rosmaster R2.

    - Subscribes to /cmd_vel (geometry_msgs/Twist)
    - Uses linear.x for forward/backward speed
    - Uses angular.z for steering (mapped to servo angle)
    """

    def __init__(self):
        super().__init__('r2_driver')

        # Parameters (can be overridden via ROS2 params)
        self.declare_parameter('max_speed', 1.0)            # m/s
        self.declare_parameter('max_steer_angle_deg', 30.0) # ± steering from center
        self.declare_parameter('servo_id', 1)               # steering servo channel
        self.declare_parameter('center_angle_deg', 90.0)
        self.declare_parameter('min_angle_deg', 45.0)
        self.declare_parameter('max_angle_deg', 135.0)
        self.declare_parameter('cmd_vel_timeout', 0.5)      # seconds
        self.declare_parameter('control_rate_hz', 20.0)     # loop rate

        self.steer_pub = self.create_publisher(Float32, 'steering_angle', 10)
        self.last_steer_delta_rad = 0.0

        self.max_speed = float(self.get_parameter('max_speed').value)
        self.max_steer_angle_deg = float(self.get_parameter('max_steer_angle_deg').value)
        self.servo_id = int(self.get_parameter('servo_id').value)
        self.center_angle = float(self.get_parameter('center_angle_deg').value)
        self.min_angle = float(self.get_parameter('min_angle_deg').value)
        self.max_angle = float(self.get_parameter('max_angle_deg').value)
        self.cmd_vel_timeout = float(self.get_parameter('cmd_vel_timeout').value)
        self.control_rate_hz = float(self.get_parameter('control_rate_hz').value)

        # Angular.z at which we apply max steering (you can tune this)
        self.ang_z_for_max_steer = 1.0  # rad/s

        self.get_logger().info("Initializing Rosmaster R2 hardware...")
        self.bot = Rosmaster(car_type=5)
        self.bot.set_car_type(5)

        # Current command state
        self.current_twist = Twist()
        self.last_cmd_time = self.get_clock().now()

        # Subscribe to /cmd_vel
        self.cmd_sub = self.create_subscription(
            Twist,
            'cmd_vel',
            self.cmd_vel_callback,
            10
        )

        # Control loop timer
        period = 1.0 / self.control_rate_hz
        self.timer = self.create_timer(period, self.control_loop)

        # Initialize steering to center
        self._send_steering(self.center_angle)

        self.get_logger().info("R2DriverNode initialized. Listening on /cmd_vel")

    def cmd_vel_callback(self, msg: Twist):
        """Store the last received Twist and timestamp."""
        self.current_twist = msg
        self.last_cmd_time = self.get_clock().now()

    def control_loop(self):
        """
        Runs at a fixed rate.
        - If cmd_vel is recent: convert it to motor + steering commands
        - If cmd_vel times out: stop and center steering
        """
        now = self.get_clock().now()
        age = (now - self.last_cmd_time).nanoseconds * 1e-9

        if age > self.cmd_vel_timeout:
            # Safety stop if no recent command
            vx = 0.0
            steering_angle = self.center_angle
        else:
            # Use the last received cmd_vel
            vx = clamp(self.current_twist.linear.x, -self.max_speed, self.max_speed)

            # Map angular.z to steering angle
            ang_z = self.current_twist.angular.z
            # Normalize angular.z into [-1, 1]
            if self.ang_z_for_max_steer > 0.0:
                norm = clamp(ang_z / self.ang_z_for_max_steer, -1.0, 1.0)
            else:
                norm = 0.0

            # teleop_twist_keyboard: +z = left, -z = right
            # For servo: smaller angle = left, larger angle = right
            steering_angle = self.center_angle - norm * self.max_steer_angle_deg

        # Clamp steering angle within mechanical limits
        steering_angle = clamp(steering_angle, self.min_angle, self.max_angle)
        # steering_angle is servo command in degrees
        delta_deg = self.center_angle - steering_angle   # left positive
        self.last_steer_delta_rad = math.radians(delta_deg)

        msg = Float32()
        msg.data = float(self.last_steer_delta_rad)
        self.steer_pub.publish(msg)

        # Send commands to hardware
        try:
            self.bot.set_car_motion(v_x=vx, v_y=0.0, v_z=0.0)
            self._send_steering(steering_angle)
        except Exception as e:
            self.get_logger().error(f"Error sending commands to Rosmaster: {e}")

    def _send_steering(self, angle_deg: float):
        """Send steering angle in degrees to servo."""
        angle_int = int(round(angle_deg))
        angle_int = int(clamp(angle_int, self.min_angle, self.max_angle))
        self.bot.set_pwm_servo(self.servo_id, angle_int)

    def destroy_node(self):
        # Stop the car on shutdown
        try:
            self.bot.set_car_motion(0.0, 0.0, 0.0)
            self._send_steering(self.center_angle)
        except Exception:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = R2DriverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("KeyboardInterrupt, shutting down r2_driver...")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
