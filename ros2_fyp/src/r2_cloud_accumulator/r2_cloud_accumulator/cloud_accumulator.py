import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup, ReentrantCallbackGroup
from sensor_msgs.msg import PointCloud2, PointField
from std_srvs.srv import Empty
import tf2_ros
import numpy as np
from numpy.lib.recfunctions import structured_to_unstructured
from sensor_msgs_py import point_cloud2


class CloudAccumulator(Node):
    def __init__(self):
        super().__init__('cloud_accumulator')

        # Parameters
        self.declare_parameter('input_topic', '/camera/depth/points')
        self.declare_parameter('output_topic', '/accumulated_cloud')
        self.declare_parameter('map_frame', 'map')
        self.declare_parameter('voxel_size', 0.03)
        self.declare_parameter('max_points', 500000)
        self.declare_parameter('max_range', 4.0)
        self.declare_parameter('min_range', 0.3)
        self.declare_parameter('max_height', 0.8)

        self.input_topic = self.get_parameter('input_topic').value
        self.output_topic = self.get_parameter('output_topic').value
        self.map_frame = self.get_parameter('map_frame').value
        self.voxel_size = self.get_parameter('voxel_size').value
        self.max_points = self.get_parameter('max_points').value
        self.max_range = self.get_parameter('max_range').value
        self.min_range = self.get_parameter('min_range').value
        self.max_height = self.get_parameter('max_height').value

        # State
        self.accumulated_points = np.empty((0, 3), dtype=np.float32)
        self.latest_cloud = None

        # Callback groups — separate so subscriber doesn't block service calls
        self._sub_group = MutuallyExclusiveCallbackGroup()
        self._srv_group = MutuallyExclusiveCallbackGroup()

        # TF buffer
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # Subscriber — best_effort QoS to match Astra camera
        sensor_qos = QoSProfile(
            depth=5,
            reliability=ReliabilityPolicy.BEST_EFFORT,
            durability=DurabilityPolicy.VOLATILE,
        )
        self.sub = self.create_subscription(
            PointCloud2, self.input_topic, self._cloud_callback, sensor_qos,
            callback_group=self._sub_group
        )

        # Publisher — reliable for RViz
        self.pub = self.create_publisher(PointCloud2, self.output_topic, 5)
        self.pub_timer = self.create_timer(1.0, self._publish_accumulated)

        # Services
        self.create_service(Empty, '~/capture', self._capture_callback,
                           callback_group=self._srv_group)
        self.create_service(Empty, '~/clear_map', self._clear_map_callback,
                           callback_group=self._srv_group)

        self.get_logger().info(
            f'Cloud accumulator (manual mode): {self.input_topic} -> {self.output_topic}\n'
            f'  Call ~/capture to add current view to map\n'
            f'  Call ~/clear_map to reset'
        )

    def _cloud_callback(self, msg: PointCloud2):
        """Just buffer the latest cloud — don't accumulate until triggered."""
        self.latest_cloud = msg

    def _capture_callback(self, request, response):
        """Service: capture the latest cloud into the accumulated map."""
        if self.latest_cloud is None:
            self.get_logger().warn('No cloud received yet — nothing to capture')
            return response

        msg = self.latest_cloud

        # Look up transform from cloud frame to map frame
        try:
            transform = self.tf_buffer.lookup_transform(
                self.map_frame, msg.header.frame_id, rclpy.time.Time(),
                rclpy.duration.Duration(seconds=0.5)
            )
        except (tf2_ros.LookupException, tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException) as e:
            self.get_logger().error(f'TF lookup failed: {e}')
            return response

        # Extract and filter points
        points = self._extract_xyz(msg)
        if points is None or len(points) == 0:
            self.get_logger().warn('Cloud was empty')
            return response

        distances = np.linalg.norm(points, axis=1)
        mask = (distances >= self.min_range) & (distances <= self.max_range)
        mask &= np.all(np.isfinite(points), axis=1)
        points = points[mask]

        if len(points) == 0:
            self.get_logger().warn('No valid points after filtering')
            return response

        # Transform to map frame
        t = transform.transform.translation
        r = transform.transform.rotation
        points_map = self._transform_points(points, t, r)

        # Filter by max height (Z in map frame)
        points_map = points_map[points_map[:, 2] <= self.max_height]
        if len(points_map) == 0:
            self.get_logger().warn('No points below max height after transform')
            return response

        # Accumulate
        self.accumulated_points = np.vstack([self.accumulated_points, points_map])

        # Voxel downsample if over limit
        if len(self.accumulated_points) > self.max_points:
            self.accumulated_points = self._voxel_downsample(
                self.accumulated_points, self.voxel_size
            )
            if len(self.accumulated_points) > self.max_points:
                self.accumulated_points = self.accumulated_points[-self.max_points:]

        self.get_logger().info(
            f'Captured! Total: {len(self.accumulated_points)} points'
        )
        return response

    def _extract_xyz(self, msg: PointCloud2):
        try:
            pts_structured = point_cloud2.read_points(
                msg, field_names=('x', 'y', 'z'), skip_nans=True
            )
            pts = structured_to_unstructured(pts_structured).astype(np.float32)
            if pts.ndim != 2 or pts.shape[0] == 0:
                return None
            return pts
        except Exception as e:
            self.get_logger().warn(f'Failed to read point cloud: {e}')
            return None

    def _transform_points(self, points, t, r):
        qx, qy, qz, qw = r.x, r.y, r.z, r.w
        rot = np.array([
            [1 - 2*(qy*qy + qz*qz), 2*(qx*qy - qz*qw),     2*(qx*qz + qy*qw)],
            [2*(qx*qy + qz*qw),     1 - 2*(qx*qx + qz*qz), 2*(qy*qz - qx*qw)],
            [2*(qx*qz - qy*qw),     2*(qy*qz + qx*qw),     1 - 2*(qx*qx + qy*qy)],
        ], dtype=np.float32)
        translation = np.array([t.x, t.y, t.z], dtype=np.float32)
        return (points @ rot.T) + translation

    def _voxel_downsample(self, points, voxel_size):
        if len(points) == 0:
            return points
        quantized = np.floor(points / voxel_size).astype(np.int32)
        _, unique_idx = np.unique(quantized, axis=0, return_index=True)
        return points[np.sort(unique_idx)]

    def _publish_accumulated(self):
        if len(self.accumulated_points) == 0:
            return
        msg = PointCloud2()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.map_frame
        msg.height = 1
        msg.width = len(self.accumulated_points)
        msg.fields = [
            PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
            PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
            PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
        ]
        msg.is_bigendian = False
        msg.point_step = 12
        msg.row_step = msg.point_step * msg.width
        msg.data = self.accumulated_points.astype(np.float32).tobytes()
        msg.is_dense = True
        self.pub.publish(msg)

    def _clear_map_callback(self, request, response):
        self.accumulated_points = np.empty((0, 3), dtype=np.float32)
        self.get_logger().info('Accumulated cloud cleared')
        return response


def main(args=None):
    rclpy.init(args=args)
    node = CloudAccumulator()
    executor = MultiThreadedExecutor(num_threads=3)
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
