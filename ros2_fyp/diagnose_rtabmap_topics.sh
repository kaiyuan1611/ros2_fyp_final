#!/bin/bash

echo "=== RTAB-Map Topic Diagnostics ==="
echo

# Source the workspace
source install/setup.bash

echo "1. Checking required topics exist..."
required_topics=("/camera/ir/image_raw" "/camera/depth/image_raw" "/camera/ir/camera_info" "/odom" "/scan")

for topic in "${required_topics[@]}"; do
    if ros2 topic list | grep -q "^$topic$"; then
        echo "✅ $topic - EXISTS"
    else
        echo "❌ $topic - MISSING"
    fi
done

echo
echo "2. Checking topic publishers and subscribers..."
for topic in "${required_topics[@]}"; do
    if ros2 topic list | grep -q "^$topic$"; then
        info=$(ros2 topic info "$topic" 2>/dev/null)
        pub_count=$(echo "$info" | grep "Publisher count:" | awk '{print $3}')
        sub_count=$(echo "$info" | grep "Subscription count:" | awk '{print $3}')
        echo "$topic: Publishers=$pub_count, Subscribers=$sub_count"
    fi
done

echo
echo "3. Checking topic data rates (5 second test)..."
for topic in "/camera/ir/image_raw" "/camera/depth/image_raw" "/odom"; do
    if ros2 topic list | grep -q "^$topic$"; then
        echo "Testing $topic..."
        timeout 5 ros2 topic hz "$topic" 2>/dev/null || echo "  No data received"
    fi
done

echo
echo "4. Checking TF tree..."
echo "Available frames:"
timeout 3 ros2 run tf2_tools view_frames 2>/dev/null || echo "TF tree check failed"

echo
echo "5. Checking camera node status..."
camera_nodes=$(ros2 node list | grep camera)
if [ -n "$camera_nodes" ]; then
    echo "Camera nodes running:"
    echo "$camera_nodes"
else
    echo "❌ No camera nodes found!"
fi

echo
echo "6. Quick topic echo test (2 seconds each)..."
for topic in "/camera/ir/image_raw" "/camera/depth/image_raw"; do
    echo "Testing $topic..."
    timeout 2 ros2 topic echo "$topic" --no-arr --once 2>/dev/null && echo "  ✅ Data received" || echo "  ❌ No data"
done

echo
echo "=== Diagnostics Complete ==="
echo
echo "If topics show 'No data received', try:"
echo "1. Restart camera: ros2 launch r2_bringup astra_camera.launch.py"
echo "2. Check camera connection: lsusb | grep -i astra"
echo "3. Use fixed launch file: ros2 launch r2_rtabmap rtabmap_ir_fixed.launch.py"