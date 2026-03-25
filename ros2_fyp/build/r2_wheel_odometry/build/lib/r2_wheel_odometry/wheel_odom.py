#!/usr/bin/env python3
import math
import time
from std_msgs.msg import Float32

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster

from Rosmaster_Lib import Rosmaster


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def yaw_to_quat(yaw: float):
    h = 0.5 * yaw
    return (0.0, 0.0, math.sin(h), math.cos(h))


class WheelOdom(Node):
    """
    Encoder + Ackermann odometry for Yahboom Rosmaster R2.
    - Reads M2 (rear-left) and M4 (rear-right) encoder ticks from Rosmaster.
    - Computes v from rear wheels.
    - Computes yaw_rate from steering inferred from /cmd_vel.angular.z (matches your driver mapping).
    - Publishes:
        /odom  (nav_msgs/Odometry)
        TF: odom -> base_footprint
    """

    def __init__(self):
        super().__init__('r2_wheel_odometry')

        # ---- Parameters ----
        self.declare_parameter('car_type', 5)
        self.declare_parameter('com', '/dev/myserial')

        self.declare_parameter('TPR', 824.15)   # ticks per wheel revolution
        self.declare_parameter('R', 0.0331)     # rear wheel radius (m)
        self.declare_parameter('L', 0.235)      # wheelbase (m)

        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_footprint')

        self.declare_parameter('rate_hz', 50.0)

        self.delta_rad = 0.0
        self.create_subscription(Float32, 'steering_angle', self.on_steer, 10)

        # Must match your driver steering mapping
        self.declare_parameter('ang_z_for_max_steer', 1.0)      # rad/s that maps to max steer
        self.declare_parameter('max_steer_angle_deg', 30.0)     # ± from center
        self.declare_parameter('center_angle_deg', 90.0)
        self.declare_parameter('min_angle_deg', 45.0)
        self.declare_parameter('max_angle_deg', 135.0)

        # If you later measure actual wheel steering angle and need scaling, set k != 1
        self.declare_parameter('steer_scale', 1.0)

        # ---- Load params ----
        self.car_type = int(self.get_parameter('car_type').value)
        self.com = str(self.get_parameter('com').value)

        self.TPR = float(self.get_parameter('TPR').value)
        self.R = float(self.get_parameter('R').value)
        self.L = float(self.get_parameter('L').value)

        self.odom_frame = str(self.get_parameter('odom_frame').value)
        self.base_frame = str(self.get_parameter('base_frame').value)
        self.rate_hz = float(self.get_parameter('rate_hz').value)

        self.ang_z_for_max_steer = float(self.get_parameter('ang_z_for_max_steer').value)
        self.max_steer_angle_deg = float(self.get_parameter('max_steer_angle_deg').value)
        self.center_angle_deg = float(self.get_parameter('center_angle_deg').value)
        self.min_angle_deg = float(self.get_parameter('min_angle_deg').value)
        self.max_angle_deg = float(self.get_parameter('max_angle_deg').value)
        self.steer_scale = float(self.get_parameter('steer_scale').value)

        # Encoder tuple is (M1, M2, M3, M4)
        self.IDX_L = 1  # M2 rear-left
        self.IDX_R = 3  # M4 rear-right

        # ---- ROS interfaces ----
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.tf_br = TransformBroadcaster(self)

        self.last_cmd = Twist()
        self.create_subscription(Twist, 'cmd_vel', self.on_cmd_vel, 10)

        # ---- Hardware init ----
        self.get_logger().info(f"Opening Rosmaster on {self.com} car_type={self.car_type} ...")
        self.bot = Rosmaster(car_type=self.car_type, com=self.com, debug=False)
        self.bot.create_receive_threading()
        self.bot.set_auto_report_state(True, forever=False)
        time.sleep(0.2)

        self.prev_enc = self.bot.get_motor_encoder()
        self.prev_t = time.monotonic()

        # ---- State ----
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0

        self.timer = self.create_timer(1.0 / self.rate_hz, self.update)
        self.get_logger().info("r2_wheel_odometry started: publishing /odom and TF odom->base_footprint")
        self.get_logger().info(f"odom_frame={self.odom_frame}, base_frame={self.base_frame}")


    def on_cmd_vel(self, msg: Twist):
        self.last_cmd = msg

    def on_steer(self, msg: Float32):
        # left positive, right negative
        self.delta_rad = float(msg.data) * self.steer_scale

    def steering_delta_rad_from_cmdvel(self) -> float:
        """
        Match your driver mapping exactly:

          norm = clamp(ang_z / ang_z_for_max_steer, -1, 1)
          steering_angle_deg = center - norm * max_steer_angle_deg
          clamp steering within [min_angle_deg, max_angle_deg]

        Physical observation:
          smaller servo angle => left

        Convert servo command -> Ackermann delta:
          delta_deg = center - steering_angle_deg  (left positive)
          delta_rad = radians(delta_deg) * steer_scale
        """
        ang_z = float(self.last_cmd.angular.z)

        if self.ang_z_for_max_steer > 0.0:
            norm = clamp(ang_z / self.ang_z_for_max_steer, -1.0, 1.0)
        else:
            norm = 0.0

        steering_angle_deg = self.center_angle_deg - norm * self.max_steer_angle_deg
        steering_angle_deg = clamp(steering_angle_deg, self.min_angle_deg, self.max_angle_deg)

        delta_deg = self.center_angle_deg - steering_angle_deg  # left positive
        return math.radians(delta_deg) * self.steer_scale

    def update(self):
        now_t = time.monotonic()
        dt = now_t - self.prev_t
        if dt <= 0.0:
            return

        enc = self.bot.get_motor_encoder()
        dL = enc[self.IDX_L] - self.prev_enc[self.IDX_L]
        dR = enc[self.IDX_R] - self.prev_enc[self.IDX_R]

        meters_per_tick = (2.0 * math.pi * self.R) / self.TPR
        vL = (dL * meters_per_tick) / dt
        vR = (dR * meters_per_tick) / dt
        v = 0.5 * (vL + vR)

        delta = self.delta_rad
        yaw_rate = (v / self.L) * math.tan(delta)

        # Integrate (planar)
        self.x += v * math.cos(self.yaw) * dt
        self.y += v * math.sin(self.yaw) * dt
        self.yaw += yaw_rate * dt

        self.publish(v, yaw_rate)

        self.prev_enc = enc
        self.prev_t = now_t

    def publish(self, v: float, yaw_rate: float):
        stamp = self.get_clock().now().to_msg()
        qx, qy, qz, qw = yaw_to_quat(self.yaw)

        odom = Odometry()
        odom.header.stamp = stamp
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame

        odom.pose.pose.position.x = float(self.x)
        odom.pose.pose.position.y = float(self.y)
        odom.pose.pose.position.z = 0.0
        odom.pose.pose.orientation.x = qx
        odom.pose.pose.orientation.y = qy
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw

        odom.twist.twist.linear.x = float(v)
        odom.twist.twist.angular.z = float(yaw_rate)

        self.odom_pub.publish(odom)

        tfm = TransformStamped()
        tfm.header.stamp = stamp
        tfm.header.frame_id = self.odom_frame
        tfm.child_frame_id = self.base_frame
        tfm.transform.translation.x = float(self.x)
        tfm.transform.translation.y = float(self.y)
        tfm.transform.translation.z = 0.0
        tfm.transform.rotation.x = qx
        tfm.transform.rotation.y = qy
        tfm.transform.rotation.z = qz
        tfm.transform.rotation.w = qw

        self.tf_br.sendTransform(tfm)


def main():
    rclpy.init()
    node = WheelOdom()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
