#!/bin/bash
# RK3568 Board Environment Check Script
# Run this script on RK3568 board

echo "================================================================"
echo "       RK3568 Board Environment Check"
echo "================================================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_ok() {
    echo -e "${GREEN}[OK]${NC} $1"
}

check_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# 1. Check system info
echo "[1/6] System Information"
echo "================================================================"
echo "Device: $(cat /proc/device-tree/model 2>/dev/null || echo 'Unknown')"
echo "Kernel: $(uname -r)"
echo "OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'=' -f2 | tr -d '\"')"
echo ""

# 2. Check NPU
echo "[2/6] NPU Status"
echo "================================================================"
if [ -d "/sys/class/misc/rknpu" ]; then
    check_ok "NPU device found"
    cat /sys/class/misc/rknpu/version 2>/dev/null && echo ""
else
    check_error "NPU device not found"
    echo "Please check NPU driver installation"
fi
echo ""

# 3. Check RKNN Runtime
echo "[3/6] RKNN Runtime"
echo "================================================================"
if [ -f "/usr/lib/librknnrt.so" ]; then
    check_ok "librknnrt.so found"
    ls -lh /usr/lib/librknnrt.so
else
    check_error "librknnrt.so not found"
    echo ""
    echo "Install RKNN Runtime:"
    echo "  1. Download from: https://github.com/rockchip-linux/rknpu2"
    echo "  2. Install: tar -xzf rknn-api.tar.gz -C /"
    echo "  3. Run: ldconfig"
fi
echo ""

# 4. Check Python
echo "[4/6] Python Environment"
echo "================================================================"
if command -v python3 &> /dev/null; then
    PYTHON_VER=$(python3 --version 2>&1)
    check_ok "$PYTHON_VER"
    
    # Check Python packages
    echo ""
    echo "Python packages:"
    
    if python3 -c "import numpy" 2>/dev/null; then
        check_ok "numpy: $(python3 -c 'import numpy; print(numpy.__version__)')"
    else
        check_warning "numpy not installed"
    fi
    
    if python3 -c "import cv2" 2>/dev/null; then
        check_ok "opencv: $(python3 -c 'import cv2; print(cv2.__version__)')"
    else
        check_warning "opencv not installed"
    fi
    
    if python3 -c "from rknn.api import RKNN" 2>/dev/null; then
        check_ok "rknn-api available"
    else
        check_error "rknn-api not available"
    fi
else
    check_error "Python3 not found"
    echo "Install: apt-get install python3 python3-pip"
fi
echo ""

# 5. Check Memory
echo "[5/6] Memory Status"
echo "================================================================"
TOTAL_MEM=$(free -m | awk '/Mem:/ {print $2}')
USED_MEM=$(free -m | awk '/Mem:/ {print $3}')
AVAIL_MEM=$(free -m | awk '/Mem:/ {print $7}')
echo "Total: ${TOTAL_MEM}MB"
echo "Used:  ${USED_MEM}MB"
echo "Available: ${AVAIL_MEM}MB"

if [ "$AVAIL_MEM" -lt 512 ]; then
    check_warning "Low memory available (<512MB)"
else
    check_ok "Sufficient memory"
fi
echo ""

# 6. Check Storage
echo "[6/6] Storage Status"
echo "================================================================"
df -h / | tail -1 | awk '{print "Root partition: " $3 " used / " $4 " available (" $5 " used)"}'
echo ""

# Summary
echo "================================================================"
echo "                    Check Complete"
echo "================================================================"
echo ""
echo "Required packages for RK3568:"
echo "  - librknnrt.so (RKNN Runtime)"
echo "  - Python 3.8+"
echo "  - numpy"
echo "  - opencv-python"
echo "  - rknn-api"
echo ""