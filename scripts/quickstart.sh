#!/bin/bash
# VPN Cloud Project - Quick Start Script

set -e

echo "=========================================="
echo "VPN Cloud Project - Quick Start"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available"
    echo "Please install Docker Compose plugin"
    exit 1
fi

echo "✓ Docker and Docker Compose are installed"
echo ""

# Generate self-signed SSL certificates for local development
echo "Generating SSL certificates for HTTPS..."
mkdir -p certs
if [ ! -f certs/privkey.pem ]; then
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout certs/privkey.pem -out certs/fullchain.pem \
        -subj "/C=IN/ST=State/L=City/O=VPN-Cloud/CN=localhost" \
        2>/dev/null
    echo "✓ SSL certificates generated"
else
    echo "✓ SSL certificates already exist"
fi
echo ""

# Build and start containers
echo "Building and starting Docker containers..."
echo "This may take a few minutes on first run..."
echo ""

docker compose up -d --build

echo ""
echo "=========================================="
echo "✓ VPN Cloud Project is starting!"
echo "=========================================="
echo ""
echo "Services:"
echo "  - Web UI:        https://localhost"
echo "  - Database:      localhost:3306"
echo "  - Squid Proxy:   localhost:3128"
echo "  - WireGuard:     localhost:51820/udp"
echo ""
echo "Default Login Credentials:"
echo "  Username: student1"
echo "  Password: password123"
echo ""
echo "  Username: demo"
echo "  Password: demo123"
echo ""
echo "Commands:"
echo "  View logs:       docker compose logs -f"
echo "  Stop services:   docker compose down"
echo "  Restart:         docker compose restart"
echo ""
echo "⚠ Note: Your browser will show a certificate warning"
echo "   This is expected for self-signed certificates"
echo "   Click 'Advanced' and 'Proceed to localhost'"
echo ""
echo "Please wait 30 seconds for all services to initialize..."
