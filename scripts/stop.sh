#!/bin/bash
# Stop all VPN services

echo "Stopping VPN Cloud Project..."
docker compose down

echo "✓ All services stopped"
echo ""
echo "To remove all data (including database):"
echo "  docker compose down -v"
