#!/bin/bash
# Setup script for Opus Clip Cloud on Oracle Cloud Ubuntu

echo "=========================================="
echo "Opus Clip Cloud - Setup Script"
echo "=========================================="
echo ""

# Check if running on Ubuntu/Debian
if [ ! -f /etc/os-release ]; then
    echo "Error: Cannot detect OS"
    exit 1
fi

. /etc/os-release
if [ "$ID" != "ubuntu" ] && [ "$ID" != "debian" ]; then
    echo "Warning: This script is designed for Ubuntu/Debian"
fi

echo "Step 1: Updating system packages..."
sudo apt update

echo ""
echo "Step 2: Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv ffmpeg git

echo ""
echo "Step 3: Creating Python virtual environment..."
python3 -m venv venv

echo ""
echo "Step 4: Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Step 5: Upgrading pip..."
pip install --upgrade pip

echo ""
echo "Step 6: Installing Python dependencies..."
pip install -r requirements_cloud.txt

echo ""
echo "Step 7: Creating necessary directories..."
mkdir -p downloads
mkdir -p outputs
mkdir -p templates
mkdir -p static
mkdir -p logs

echo ""
echo "Step 8: Setting permissions..."
chmod +x setup_cloud.sh
chmod +x run_cloud.sh

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Test the application:"
echo "   ./run_cloud.sh"
echo ""
echo "2. For production deployment with systemd:"
echo "   sudo cp opus-clip-cloud.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable opus-clip-cloud"
echo "   sudo systemctl start opus-clip-cloud"
echo ""
echo "3. Check status:"
echo "   sudo systemctl status opus-clip-cloud"
echo ""
echo "4. View logs:"
echo "   sudo journalctl -u opus-clip-cloud -f"
echo ""
echo "5. Configure firewall (if not done already):"
echo "   sudo iptables -I INPUT -p tcp --dport 5000 -j ACCEPT"
echo "   sudo netfilter-persistent save"
echo ""
