#!/bin/bash

echo "=== RTAB-Map Installation Check ==="
echo

# Check if RTAB-Map packages are installed
echo "1. Checking RTAB-Map packages..."
if ros2 pkg list | grep -q rtabmap; then
    echo "✅ RTAB-Map packages found:"
    ros2 pkg list | grep rtabmap | sed 's/^/   /'
else
    echo "❌ RTAB-Map packages not found!"
    echo "   Install with: sudo apt install ros-humble-rtabmap-ros"
    exit 1
fi

echo

# Check if our custom package built successfully
echo "2. Checking r2_rtabmap package..."
if ros2 pkg list | grep -q r2_rtabmap; then
    echo "✅ r2_rtabmap package found"
else
    echo "❌ r2_rtabmap package not found!"
    echo "   Build with: colcon build --packages-select r2_rtabmap"
    exit 1
fi

echo

# Check launch files
echo "3. Checking launch files..."
launch_files=(
    "rtabmap_simple.launch.py"
    "rtabmap_full_system.launch.py" 
    "rtabmap_mapping.launch.py"
    "rtabmap_with_config.launch.py"
    "rtabmap_ir_optimized.launch.py"
)

for file in "${launch_files[@]}"; do
    if [ -f "src/r2_rtabmap/launch/$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file missing"
    fi
done

echo

# Check config file
echo "4. Checking configuration file..."
if [ -f "src/r2_rtabmap/config/rtabmap_config.yaml" ]; then
    echo "✅ rtabmap_config.yaml"
else
    echo "❌ rtabmap_config.yaml missing"
fi

echo

# Check if required topics would be available (basic check)
echo "5. Checking system readiness (IR Camera)..."
echo "   Required topics for RTAB-Map with IR camera:"
echo "   - /camera/ir/image_raw (IR image - used as RGB input)"
echo "   - /camera/depth/image_raw (Depth image)" 
echo "   - /camera/ir/camera_info (IR camera info)"
echo "   - /camera/depth/camera_info (Depth camera info)"
echo "   - /odom (Odometry)"
echo "   - /scan (Laser scan - optional but recommended for IR)"
echo
echo "   To verify topics are available, run:"
echo "   ros2 topic list | grep -E '(camera|odom|scan)'"

echo

echo "=== Installation Check Complete ==="
echo
echo "Next steps:"
echo "1. Source the workspace: source install/setup.bash"
echo "2. Start with IR-optimized test: ros2 launch r2_rtabmap rtabmap_ir_optimized.launch.py"
echo "3. See IR_CAMERA_RTABMAP_GUIDE.md for IR-specific instructions"
echo "4. See RTABMAP_SETUP_GUIDE.md for general setup information"