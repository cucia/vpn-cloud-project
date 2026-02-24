#!/usr/bin/env python3
"""
VPN Cloud Project - Linux CLI Client
Connects to VPN server using username/password authentication
"""

import sys
import os
import requests
import getpass
import subprocess
import argparse
import json
from pathlib import Path

API_BASE_URL = "https://localhost/api"
CONFIG_DIR = Path.home() / ".config" / "vpn-connect"
CONFIG_FILE = CONFIG_DIR / "config.json"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_success(msg):
    print(f"{Colors.GREEN}✓{Colors.ENDC} {msg}")

def print_error(msg):
    print(f"{Colors.RED}✗{Colors.ENDC} {msg}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ{Colors.ENDC} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠{Colors.ENDC} {msg}")

def check_root():
    """Check if running as root (required for WireGuard)"""
    if os.geteuid() != 0:
        print_error("This command requires root privileges")
        print_info("Please run with sudo: sudo wg-connect")
        sys.exit(1)

def check_dependencies():
    """Check if WireGuard is installed"""
    try:
        subprocess.run(['wg', '--version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("WireGuard is not installed")
        print_info("Install with: sudo apt install wireguard-tools")
        return False

def save_config(server_url):
    """Save server configuration"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    config = {'server_url': server_url}
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)
    print_success(f"Configuration saved to {CONFIG_FILE}")

def load_config():
    """Load server configuration"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None

def authenticate(http_session, server_url, username, password):
    """Authenticate with VPN server"""
    print_info(f"Authenticating as {username}...")

    try:
        response = http_session.post(
            f"{server_url}/auth/login",
            json={'username': username, 'password': password},
            timeout=10
        )

        if response.status_code == 200:
            print_success("Authentication successful")
            return True
        else:
            error = response.json().get('error', 'Unknown error')
            print_error(f"Authentication failed: {error}")
            return False

    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {e}")
        print_info("Make sure the VPN server is running and accessible")
        return False

    def generate_config(http_session, server_url):
    """Generate WireGuard configuration from server"""
    print_info("Generating VPN configuration...")

    try:
        response = http_session.post(
            f"{server_url}/config/generate",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print_success(f"Configuration generated (IP: {data['assigned_ip']})")
            return data['config']
        else:
            print_error("Failed to generate configuration")
            return None

    except requests.exceptions.RequestException as e:
        print_error(f"Connection error: {e}")
        return None

def connect_vpn(config):
    """Connect to VPN using WireGuard"""
    print_info("Establishing VPN connection...")

    # Save config to temporary file
    config_path = Path("/tmp/wg0.conf")
    with open(config_path, 'w') as f:
        f.write(config)

    try:
        # Bring up WireGuard interface
        subprocess.run(['wg-quick', 'up', str(config_path)], check=True)
        print_success("VPN connected successfully!")
        print_info("Only YouTube is accessible through this VPN")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to establish VPN connection: {e}")
        return False
    finally:
        # Clean up config file
        if config_path.exists():
            config_path.unlink()

def disconnect_vpn():
    """Disconnect from VPN"""
    check_root()
    print_info("Disconnecting VPN...")

    try:
        subprocess.run(['wg-quick', 'down', 'wg0'], check=True)
        print_success("VPN disconnected")
    except subprocess.CalledProcessError:
        print_error("No active VPN connection found")

def show_status():
    """Show VPN connection status"""
    try:
        result = subprocess.run(['wg', 'show', 'wg0'], 
                              capture_output=True, text=True, check=True)
        print_success("VPN Status:")
        print(result.stdout)
    except subprocess.CalledProcessError:
        print_info("VPN is not connected")

def setup_wizard():
    """Interactive setup wizard"""
    print(f"{Colors.BOLD}VPN Connect - Setup Wizard{Colors.ENDC}")
    print("=" * 50)

    server_url = input("Enter VPN server URL (e.g., https://vpn.example.com/api): ").strip()
    save_config(server_url)

    print_success("Setup complete!")
    print_info("You can now connect with: wg-connect <username>")

def main():
    parser = argparse.ArgumentParser(description='VPN Cloud Project - CLI Client')
    parser.add_argument('username', nargs='?', help='VPN username')
    parser.add_argument('--setup', action='store_true', help='Run setup wizard')
    parser.add_argument('--disconnect', action='store_true', help='Disconnect from VPN')
    parser.add_argument('--status', action='store_true', help='Show VPN status')
    parser.add_argument('--server', help='VPN server URL')

    args = parser.parse_args()

    # Suppress SSL warnings for dev (self-signed certs)
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    http_session = requests.Session()
    http_session.verify = False

    if args.setup:
        setup_wizard()
        return

    if args.disconnect:
        disconnect_vpn()
        return

    if args.status:
        show_status()
        return

    if not args.username:
        parser.print_help()
        return

    # Check dependencies
    if not check_dependencies():
        sys.exit(1)

    check_root()

    # Get server URL
    config = load_config()
    server_url = args.server or (config['server_url'] if config else None)

    if not server_url:
        print_error("Server URL not configured")
        print_info("Run: wg-connect --setup")
        sys.exit(1)

    # Get password
    password = getpass.getpass("Password: ")

    # Authenticate
    is_authenticated = authenticate(http_session, server_url, args.username, password)
    if not is_authenticated:
        sys.exit(1)

    # Generate config
    vpn_config = generate_config(http_session, server_url)
    if not vpn_config:
        sys.exit(1)

    # Connect
    if connect_vpn(vpn_config):
        print_info("Press Ctrl+C to disconnect, or run: wg-connect --disconnect")
    else:
        sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
        print_info("Interrupted by user")
        sys.exit(0)
