#!/usr/bin/env python3
import math
import time
from std_msgs.msg import Float32

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
from tf2_ros import TransformBroadcaster

from Rosmaster_Lib import Rosmaster


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def yaw_to_quat(yaw: float):
    h = 0.5 * yaw
    return (0.0, 0.0, math.sin(h), math.cos(h))


class WheelOdomAndImu(Node):
    """
    Encoder + Ackermann odometry + IMU publisher for Yahboom Rosmaster R2.
    Publishes: /odom, /imu/data_raw, TF odom->base_footprint
    """

    def __init__(self):
        super().__init__('r2_wheel_odometry_and_imu')

        # ---- Parameters ----
        self.declare_parameter('car_type', 5)
        self.declare_parameter('com', '/dev/myserial')
        self.declare_parameter('TPR', 824.15)
        self.declare_parameter('R', 0.0331)
        self.declare_parameter('L', 0.235)
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_footprint')
        self.declare_parameter('imu_frame', 'base_link')
        self.declare_parameter('rate_hz', 50.0)
        self.declare_parameter('publish_tf', True)

        self.delta_rad = 0.0
        self.create_subscription(Float32, 'steering_angle', self.on_steer, 10)

        self.declare_parameter('ang_z_for_max_steer', 1.0)
        self.declare_parameter('max_steer_angle_deg', 30.0)
        self.declare_parameter('center_angle_deg', 90.0)
        self.declare_parameter('min_angle_deg', 45.0)
        self.declare_parameter('max_angle_deg', 135.0)
        self.declare_parameter('steer_scale', 1.0)

        # ---- Load params ----
        self.car_type = int(self.get_parameter('car_type').value)
        self.com = str(self.get_parameter('com').value)
        self.TPR = float(self.get_parameter('TPR').value)
        self.R = float(self.get_parameter('R').value)
        self.L = float(self.get_parameter('L').value)
        self.odom_frame = str(self.get_parameter('odom_frame').value)
        self.base_frame = str(self.get_parameter('base_frame').value)
        self.imu_frame = str(self.get_parameter('imu_frame').value)
        self.rate_hz = float(self.get_parameter('rate_hz').value)
        self.publish_tf_enabled = bool(self.get_parameter('publish_tf').value)
        self.ang_z_for_max_steer = float(self.get_parameter('ang_z_for_max_steer').value)
        self.max_steer_angle_deg = float(self.get_parameter('max_steer_angle_deg').value)
        self.center_angle_deg = float(self.get_parameter('center_angle_deg').value)
        self.min_angle_deg = float(self.get_parameter('min_angle_deg').value)
        self.max_angle_deg = float(self.get_parameter('max_angle_deg').value)
        self.steer_scale = float(self.get_parameter('steer_scale').value)

        self.IDX_L = 1  # M2 rear-left
        self.IDX_R = 3  # M4 rear-right

        # ---- ROS interfaces ----
        self.odom_pub = self.create_publisher(Odometry, '/odom', 10)
        self.imu_pub = self.create_publisher(Imu, '/imu/data_raw', 10)
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
        self.get_logger().info("Publishing /odom, /imu/data_raw, TF odom->base_footprint")

    def on_cmd_vel(self, msg: Twist):
        self.last_cmd = msg

    def on_steer(self, msg: Float32):
        self.delta_rad = float(msg.data) * self.steer_scale

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

        self.x += v * math.cos(self.yaw) * dt
        self.y += v * math.sin(self.yaw) * dt
        self.yaw += yaw_rate * dt

        self.publish_odom(v, yaw_rate)
        self.publish_imu()

        self.prev_enc = enc
        self.prev_t = now_t

    def publish_odom(self, v: float, yaw_rate: float):
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

        if self.publish_tf_enabled:
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

    def publish_imu(self):
        """Read IMU from Rosmaster board and publish as sensor_msgs/Imu."""
        ax, ay, az = self.bot.get_accelerometer_data()
        gx, gy, gz = self.bot.get_gyroscope_data()

        imu_msg = Imu()
        imu_msg.header.stamp = self.get_clock().now().to_msg()
        imu_msg.header.frame_id = self.imu_frame

        # Orientation unknown — set covariance[0] to -1 per REP-145
        imu_msg.orientation_covariance[0] = -1.0

        # Angular velocity (rad/s)
        imu_msg.angular_velocity.x = float(gx)
        imu_msg.angular_velocity.y = float(gy)
        imu_msg.angular_velocity.z = float(gz)

        # Linear acceleration (m/s^2)
        imu_msg.linear_acceleration.x = float(ax)
        imu_msg.linear_acceleration.y = float(ay)
        imu_msg.linear_acceleration.z = float(az)

        self.imu_pub.publish(imu_msg)


def main():
    rclpy.init()
    node = WheelOdomAndImu()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
