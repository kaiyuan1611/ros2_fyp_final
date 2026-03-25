#!/bin/bash

echo "=== RTAB-Map Quick Start Test ==="
echo
echo "This script will help you test RTAB-Map step by step."
echo "Make sure to run each step in a separate terminal."
echo

# Source the workspace
source install/setup.bash

echo "Step 1: Start robot base system"
echo "Command: ros2 launch r2_bringup bringup.launch.py"
echo "Press Enter when this is running in another terminal..."
read -p ""

echo
echo "Step 2: Start Astra camera"
echo "Command: ros2 launch r2_bringup astra_camera.launch.py"
echo "Press Enter when this is running in another terminal..."
read -p ""

echo
echo "Step 3: Verify topics are available"
echo "Checking required topics..."

# Check topics
echo "Available camera topics:"
timeout 3 ros2 topic list | grep camera || echo "❌ No camera topics found"
echo "Expected topics: /camera/ir/image_raw, /camera/depth/image_raw"

echo "Available odometry topics:"
timeout 3 ros2 topic list | grep odom || echo "❌ No odometry topics found"

echo "Available scan topics (optional):"
timeout 3 ros2 topic list | grep scan || echo "ℹ️  No scan topics (optional for RTAB-Map)"

echo
echo "Step 4: Start RTAB-Map"
echo "Choose an option:"
echo "1) Simple test (recommended first time)"
echo "2) Full system with all features"
echo "3) Configuration file based"
echo "4) IR-optimized (recommended for IR+Depth cameras)"
echo

read -p "Enter choice (1-4): " choice

case $choice in
    1)
        echo "Starting simple RTAB-Map test..."
        echo "Command: ros2 launch r2_rtabmap rtabmap_simple.launch.py"
        ros2 launch r2_rtabmap rtabmap_simple.launch.py
        ;;
    2)
        echo "Starting full RTAB-Map system..."
        echo "Command: ros2 launch r2_rtabmap rtabmap_full_system.launch.py"
        ros2 launch r2_rtabmap rtabmap_full_system.launch.py
        ;;
    3)
        echo "Starting RTAB-Map with configuration file..."
        echo "Command: ros2 launch r2_rtabmap rtabmap_with_config.launch.py"
        ros2 launch r2_rtabmap rtabmap_with_config.launch.py
        ;;
    4)
        echo "Starting IR-optimized RTAB-Map..."
        echo "Command: ros2 launch r2_rtabmap rtabmap_ir_optimized.launch.py"
        ros2 launch r2_rtabmap rtabmap_ir_optimized.launch.py
        ;;
    *)
        echo "Invalid choice. Starting simple test..."
        ros2 launch r2_rtabmap rtabmap_simple.launch.py
        ;;
esac