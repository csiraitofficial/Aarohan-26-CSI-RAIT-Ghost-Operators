#!/bin/bash

# --- OSIRIS NIDS: Raspberry Pi One-Touch Deployment ---
# This script automates system setup, dependency installation, and launch.
# Run as: chmod +x pi_setup_and_run.sh && sudo ./pi_setup_and_run.sh

set -e # Exit on error

echo "🛡️ Starting {O.S.I.R.I.S} NIDS Deployment for Raspberry Pi..."

# 1. Root Check
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root (use sudo)."
   exit 1
fi

# 2. System Dependency Installation
echo "📥 Installing System Dependencies (libpcap, redis)..."
apt update
apt install -y python3-pip python3-venv libpcap-dev redis-server ethtool tshark

# 3. Service Management
# echo "⚙️ Ensuring services are active..."
# systemctl start mongodb || echo "⚠️ MongoDB start failed/not installed as service"
# systemctl start redis-server || echo "⚠️ Redis start failed/not installed as service"
# systemctl enable mongodb
# systemctl enable redis-server

# 4. Virtual Environment Setup
echo "🐍 Setting up Python Virtual Environment..."
cd "$(dirname "$0")/../backend"
if [ ! -d "venv" ]; then
    python3 -m venv venv    
fi
source venv/bin/activate

# 5. Requirement Installation
echo "📦 Installing Python Packages (this may take a few minutes)..."
pip install --upgrade pip
pip install -r requirements.txt

# 6. Industrial Environment Setup
echo "🔐 Configuring Industrial-Grade Environment..."
if [ ! -f ".env" ]; then
    if [ -f ".env.pi" ]; then
        cp .env.pi .env
        echo "✅ Created .env from .env.pi template."
    else
        echo "⚠️ .env.pi template missing. Please create .env manually!"
    fi
fi

# 7. Hardware Optimization (Interface)
INTERFACE=$(grep "INTERFACE=" .env | cut -d'=' -f2 | tr -d '"' | tr -d ' ' || echo "eth0")

echo "🚀 Attempting to optimize Interface: $INTERFACE..."

# Check if the interface exists
if ! ip link show "$INTERFACE" > /dev/null 2>&1; then
    echo "⚠️  Interface '$INTERFACE' not found. Searching for Linux defaults..."
    if ip link show wlan0 > /dev/null 2>&1; then
        INTERFACE="wlan0"
    elif ip link show eth0 > /dev/null 2>&1; then
        INTERFACE="eth0"
    else
        # Find first non-loopback interface
        INTERFACE=$(ip -o link show | awk '{print $2}' | grep -v "lo" | head -n 1 | cut -d':' -f1)
    fi
    echo "� Auto-detected interface: $INTERFACE. Please update your .env to avoid this warning."
fi

echo "🛡️  Applying hardware tweaks to $INTERFACE..."
ip link set "$INTERFACE" promisc on || echo "⚠️  Could not set promiscuous mode."
ethtool -K "$INTERFACE" gro off || echo "⚠️  GRO offload not supported on this interface."

# 8. Final Verification
echo "🔍 Verifying Elite Models..."
if [ ! -f "app/ml_models/nids_hybrid_elite.pth" ]; then
    echo "⚠️ Elite Hybrid model missing! Running bootstrap script..."
    # Use venv python for bootstrap
    ./venv/bin/python3 scripts/bootstrap_ml.py || echo "⚠️ Bootstrap failed. Models must be manually placed."
fi

# 9. Launch
echo "⚡ LAUNCHING GHOST OPERATORS NIDS APPLIANCE..."

# FIX: Help NumPy/OpenBLAS avoid 'Illegal instruction' on some Pi kernels/CPU versions
export OPENBLAS_CORETYPE=ARMV8

# FIX: Run with sudo but use the VENV's python specifically to avoid 'ModuleNotFoundError'
# This ensures it has root permissions for net-capture but uses the venv's installed modules.
echo "🛡️  Running as ROOT using Venv Context..."
sudo ./venv/bin/python3 -m app.main
