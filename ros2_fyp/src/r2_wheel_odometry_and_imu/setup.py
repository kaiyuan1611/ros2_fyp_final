from setuptools import find_packages, setup

package_name = 'r2_wheel_odometry_and_imu'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='tee',
    maintainer_email='tee@todo.todo',
    description='Wheel odometry and IMU publisher for Yahboom Rosmaster R2',
    license='MIT',
    entry_points={
        'console_scripts': [
            'wheel_odom_and_imu = r2_wheel_odometry_and_imu.wheel_odom_and_imu:main',
        ],
    },
)
