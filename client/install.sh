#!/bin/bash
# VPN Connect Client - Installation Script

set -e

echo "Installing VPN Connect CLI Client..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Install dependencies
echo "Installing dependencies..."
apt-get update
apt-get install -y python3 python3-pip wireguard-tools

# Install Python packages
pip3 install requests

# Copy client to system
echo "Installing wg-connect..."
cp wg_connect.py /usr/local/bin/wg-connect
chmod +x /usr/local/bin/wg-connect

echo "✓ Installation complete!"
echo ""
echo "Usage:"
echo "  wg-connect --setup          # First-time setup"
echo "  wg-connect <username>       # Connect to VPN"
echo "  wg-connect --status         # Show status"
echo "  wg-connect --disconnect     # Disconnect"
