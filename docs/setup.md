# Setup Guide - VPN Cloud Project

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Configuration](#configuration)
4. [Client Setup](#client-setup)
5. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended) or macOS
- **RAM**: Minimum 2GB, Recommended 4GB
- **Disk Space**: 5GB free space
- **Network**: Open ports 51820/UDP, 443/TCP

### Software Requirements

1. **Docker** (version 20.10+)
   ```bash
   # Ubuntu/Debian
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh

   # Add user to docker group
   sudo usermod -aG docker $USER
   newgrp docker
   ```

2. **Docker Compose** (comes with Docker Desktop)
   ```bash
   # Verify installation
   docker compose version
   ```

3. **Git** (for cloning updates)
   ```bash
   sudo apt-get install git
   ```

## Local Development Setup

### Step 1: Extract Project

```bash
# Extract the zip file
unzip vpn-cloud-project.zip
cd vpn-cloud-project

# Verify structure
ls -la
```

You should see:
```
docker-compose.yml
wireguard/
db/
squid/
webui/
nginx/
client/
scripts/
docs/
README.md
```

### Step 2: Generate SSL Certificates

For local development, we use self-signed certificates:

```bash
# Create certificates directory
mkdir -p certs

# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout certs/privkey.pem \
    -out certs/fullchain.pem \
    -subj "/C=IN/ST=YourState/L=YourCity/O=VPN-Cloud/CN=localhost"
```

### Step 3: Build and Start Services

```bash
# Option 1: Using quickstart script (recommended)
chmod +x scripts/quickstart.sh
./scripts/quickstart.sh

# Option 2: Manual start
docker compose up -d --build
```

Wait 30-60 seconds for all services to initialize.

### Step 4: Verify Services

```bash
# Check all containers are running
docker compose ps

# Expected output:
# NAME                    STATUS
# vpn-wireguard          Up
# vpn-database           Up (healthy)
# vpn-proxy              Up
# vpn-webui-api          Up
# vpn-nginx              Up
# restriction-server     Up

# Check logs
docker compose logs -f
```

### Step 5: Access Web UI

1. Open browser to `https://localhost`
2. Accept the self-signed certificate warning:
   - Click "Advanced"
   - Click "Proceed to localhost"
3. Login with test credentials:
   - Username: `student1`
   - Password: `password123`

## Configuration

### Database Configuration

#### Adding Users

```bash
# Connect to database
docker compose exec db mysql -u root -p
# Password: root_secure_pass_123

# Switch to database
USE vpn_users;

# Add new user
INSERT INTO vpn_users (username, password_hash, email, enabled) 
VALUES ('newuser', SHA2('newpassword', 256), 'user@example.com', TRUE);

# Verify
SELECT username, email, enabled, created_at FROM vpn_users;

# Exit
exit;
```

#### Viewing Active Connections

```sql
SELECT 
    u.username,
    ac.assigned_ip,
    ac.connected_at,
    ac.last_handshake
FROM active_connections ac
JOIN vpn_users u ON ac.user_id = u.id;
```

### Proxy Configuration

#### Adding Allowed Domains

Edit `squid/squid.conf`:

```bash
nano squid/squid.conf
```

Add domains to the YouTube ACL:

```
acl youtube dstdomain .youtube.com
acl youtube dstdomain .googlevideo.com
acl youtube dstdomain .ytimg.com
acl youtube dstdomain .ggpht.com
acl youtube dstdomain .googleapis.com  # Add new domain
```

Restart Squid:

```bash
docker compose restart squid
```

### Web UI Configuration

#### Changing Secret Key

Edit `docker-compose.yml`:

```yaml
webui:
  environment:
    SECRET_KEY: your-new-secure-secret-key-here
```

Restart webui:

```bash
docker compose restart webui
```

### WireGuard Configuration

#### Getting Server Public Key

```bash
docker compose exec wireguard wg show wg0 public-key
```

#### Viewing Connected Peers

```bash
docker compose exec wireguard wg show
```

## Client Setup

### Linux CLI Client

#### Installation

```bash
cd client
chmod +x install.sh
sudo ./install.sh
```

#### First-Time Setup

```bash
sudo wg-connect --setup
```

Enter your server URL:
- Local: `https://localhost/api`
- Production: `https://vpn.yourdomain.com/api`

#### Connecting

```bash
# Connect with username
sudo wg-connect student1

# Enter password when prompted
Password: ********

# You should see:
# ✓ Authentication successful
# ✓ Configuration generated (IP: 10.13.13.2)
# ✓ VPN connected successfully!
```

#### Checking Status

```bash
sudo wg-connect --status
```

#### Disconnecting

```bash
sudo wg-connect --disconnect
```

### Desktop WireGuard Client

1. Generate config from web dashboard
2. Download the `.conf` file
3. Import into WireGuard client:
   - **Linux**: `wg-quick up ./wg0.conf`
   - **Windows/Mac**: Import via WireGuard GUI

## Testing

### Test YouTube Access

```bash
# Should work
curl -I https://www.youtube.com

# Should be redirected
curl -I https://www.google.com
```

### Test Web API

```bash
# Login
curl -k -X POST https://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"student1","password":"password123"}'

# Get status
curl -k https://localhost/api/status
```

### Test Database Connection

```bash
# From host
docker compose exec db mysqladmin -u vpn_api -p ping
# Password: vpn_api_pass_456
```

## Troubleshooting

### Services Not Starting

**Issue**: Containers fail to start

**Solution**:
```bash
# Check logs
docker compose logs <service-name>

# Common fixes:
# 1. Port already in use
sudo netstat -tulpn | grep -E '51820|443|3306'

# 2. Permission issues
sudo chown -R $USER:$USER .

# 3. Clean restart
docker compose down -v
docker compose up -d --build
```

### Database Connection Errors

**Issue**: Web UI can't connect to database

**Solution**:
```bash
# Check database is running
docker compose ps db

# Verify network
docker compose exec webui ping db

# Check credentials in docker-compose.yml
```

### SSL Certificate Errors

**Issue**: Browser shows security warnings

**Solution**:
- This is normal for self-signed certificates in development
- Click "Advanced" → "Proceed to localhost"
- For production, use Let's Encrypt or AWS ACM

### WireGuard Connection Fails

**Issue**: VPN client can't connect

**Solution**:
```bash
# Check WireGuard is running
docker compose exec wireguard wg show

# Verify port is open
sudo ufw allow 51820/udp  # If using UFW

# Check server logs
docker compose logs wireguard
```

### YouTube Not Loading

**Issue**: YouTube doesn't work even when connected

**Solution**:
```bash
# Check Squid configuration
docker compose exec squid cat /etc/squid/squid.conf

# Verify Squid is running
docker compose logs squid

# Test proxy manually
curl -x http://localhost:3128 https://www.youtube.com
```

### Restricted Page Not Showing

**Issue**: Blocked sites don't show restriction page

**Solution**:
```bash
# Check restriction server
docker compose ps restriction-server

# Test directly
curl http://localhost:8080

# Verify Squid redirect
grep deny_info squid/squid.conf
```

## Performance Optimization

### Increase Database Pool

Edit `docker-compose.yml`:

```yaml
db:
  command: --max_connections=200
```

### Enable Squid Caching

Edit `squid/squid.conf`:

```
cache_mem 512 MB
maximum_object_size 100 MB
cache_dir ufs /var/spool/squid 1000 16 256
```

### Resource Limits

```yaml
webui:
  deploy:
    resources:
      limits:
        cpus: '0.5'
        memory: 512M
```

## Backup and Restore

### Backup Database

```bash
# Create backup
docker compose exec db mysqldump -u root -p vpn_users > backup.sql

# With timestamp
docker compose exec db mysqldump -u root -p vpn_users > backup_$(date +%Y%m%d).sql
```

### Restore Database

```bash
# Restore from backup
docker compose exec -T db mysql -u root -p vpn_users < backup.sql
```

### Backup Configuration

```bash
# Backup all configs
tar -czf vpn-backup.tar.gz \
    docker-compose.yml \
    squid/ \
    nginx/ \
    db/ \
    certs/
```

## Next Steps

- [ ] Customize allowed domains in Squid
- [ ] Add more users to database
- [ ] Set up monitoring with Grafana
- [ ] Plan AWS migration
- [ ] Implement backup automation
- [ ] Configure log rotation

## Support Resources

- README.md - General overview
- docs/aws-migration.md - Cloud deployment
- GitHub Issues - Report problems
- Docker Documentation - https://docs.docker.com

---

For additional help, check the main README or review service logs.
