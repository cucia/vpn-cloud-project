# VPN Cloud Project

**YouTube-Only VPN System with WireGuard Protocol**

A complete, containerized VPN solution designed for academic purposes that restricts internet access to YouTube only. Built with Docker, WireGuard, and modern web technologies.

## 🎯 Project Overview

This project implements a full-stack VPN system with:
- **WireGuard VPN Server** for secure, high-performance tunneling
- **Web-based Management UI** for user authentication and configuration
- **Squid Proxy** for YouTube-only access enforcement
- **MySQL Database** for user management
- **Linux CLI Client** for easy connection

### Key Features

✅ **YouTube-Only Access** - Only YouTube domains are accessible  
✅ **User Authentication** - Username/password based access control  
✅ **Web Dashboard** - Modern, responsive web interface  
✅ **Auto-Generated Configs** - Dynamic WireGuard configuration generation  
✅ **Docker-based** - Fully containerized for easy deployment  
✅ **AWS-Ready** - Designed for cloud migration  
✅ **Academic-Friendly** - Clear documentation and test credentials

## 📋 Requirements

- Docker and Docker Compose
- Linux system (for client)
- 2GB RAM minimum
- Open ports: 51820/UDP (WireGuard), 443/TCP (HTTPS)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Extract the project
unzip vpn-cloud-project.zip
cd vpn-cloud-project

# Create environment file
cp .env.example .env
```

Update `.env` before first run:
- `SECRET_KEY`
- `DB_PASSWORD`
- `MYSQL_ROOT_PASSWORD`
- `WIREGUARD_PUBLIC_KEY`
- `SERVER_ENDPOINT` (public IP or DNS with `:51820`)

Linux/macOS:

```bash

# Run the quick start script
chmod +x scripts/quickstart.sh
./scripts/quickstart.sh
```

Windows PowerShell:

```powershell
./scripts/quickstart.ps1
```

### 2. Access the Web UI

Open your browser and navigate to:
```
https://localhost
```

**Note:** You'll see a certificate warning (expected for self-signed certs). Click "Advanced" → "Proceed to localhost"

### 3. Login

Use these test credentials:

| Username | Password |
|----------|----------|
| student1 | password123 |
| demo | demo123 |
| testuser | testpass123 |
| admin | admin@vpn2025 |

### 4. Generate VPN Configuration

1. Click "Generate Config" in the dashboard
2. Download the configuration file
3. Import into WireGuard client

## 🖥️ Linux CLI Client

### Installation

```bash
cd client
sudo ./install.sh
```

### Usage

```bash
# First-time setup
sudo wg-connect --setup

# Connect to VPN
sudo wg-connect student1

# Check status
sudo wg-connect --status

# Disconnect
sudo wg-connect --disconnect
```

## 📁 Project Structure

```
vpn-cloud-project/
├── docker-compose.yml          # Main orchestration file
├── wireguard/                  # WireGuard configuration
├── db/                         # Database initialization
│   └── init.sql               # User tables and test data
├── squid/                      # Proxy server
│   ├── Dockerfile
│   ├── squid.conf             # YouTube-only ACL
│   └── blocked.html           # Restriction page
├── webui/                      # Web application
│   ├── src/                   # Flask backend
│   ├── templates/             # HTML templates
│   └── static/                # CSS, JavaScript
├── nginx/                      # Reverse proxy
│   ├── nginx.conf             # SSL configuration
│   └── restricted.html        # Blocked sites page
├── client/                     # Linux CLI client
│   ├── wg_connect.py
│   └── install.sh
├── scripts/                    # Utility scripts
└── docs/                       # Documentation
```

## 🔧 Configuration

### Environment Variables

Edit `docker-compose.yml` to customize:

```yaml
DB_HOST: db
DB_USER: vpn_api
DB_PASSWORD: vpn_api_pass_456    # Change in production!
DB_NAME: vpn_users
SECRET_KEY: change_this_secret   # Change in production!
```

### Adding Users

Connect to the database:

```bash
docker compose exec db mysql -u root -p vpn_users
```

Add a user:

```sql
INSERT INTO vpn_users (username, password_hash, email) 
VALUES ('newuser', SHA2('newpassword', 256), 'user@example.com');
```

### Customizing Allowed Domains

Edit `squid/squid.conf`:

```
acl youtube dstdomain .youtube.com .googlevideo.com .ytimg.com
# Add more domains here
```

## 📊 Service Endpoints

| Service | URL/Port | Description |
|---------|----------|-------------|
| Web UI | https://localhost | Main dashboard |
| Database | localhost:3306 | MySQL database |
| Squid Proxy | localhost:3128 | HTTP proxy |
| WireGuard | localhost:51820/udp | VPN endpoint |
| Restriction Server | localhost:8080 | Blocked page |

## 🔍 Monitoring

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f webui
docker compose logs -f wireguard
docker compose logs -f squid
```

### Check Service Status

```bash
docker compose ps
```

### Database Access

```bash
docker compose exec db mysql -u vpn_api -p vpn_users
```

## 🛑 Stopping Services

```bash
# Stop services (keep data)
docker compose down

# Stop and remove all data
docker compose down -v
```

## ☁️ AWS Migration

### Preparation

1. **Build and tag images:**
```bash
docker compose build
docker tag vpn-cloud-project-webui:latest your-ecr-repo/webui:latest
```

2. **Create ECR repositories:**
```bash
aws ecr create-repository --repository-name vpn-cloud-webui
aws ecr create-repository --repository-name vpn-cloud-squid
```

3. **Push to ECR:**
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

docker push <account>.dkr.ecr.us-east-1.amazonaws.com/vpn-cloud-webui:latest
```

### AWS Free Tier Deployment

Recommended setup for free tier:
- **2x t2.micro EC2 instances** (VPN + DB)
- **Use RDS Free Tier** for MySQL (optional)
- **Application Load Balancer** (free tier: 750 hours/month)
- **EBS Storage**: 30 GB (within free tier)

See `docs/aws-migration.md` for detailed instructions.

## 🧪 Testing

### Test YouTube Access

1. Connect to VPN
2. Visit `https://www.youtube.com` - Should work ✅
3. Visit any other site - Should see restriction page ❌

### Test Authentication

```bash
curl -k -X POST https://localhost/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"student1","password":"password123"}'
```

## 🐛 Troubleshooting

### "Connection refused" on Web UI

- Wait 30 seconds for services to initialize
- Check logs: `docker compose logs nginx webui`
- Verify containers are running: `docker compose ps`

### WireGuard client can't connect

- Check server public key in configuration
- Verify UDP port 51820 is open
- Check firewall rules

### Database connection errors

- Ensure database is running: `docker compose ps db`
- Check credentials in environment variables
- View database logs: `docker compose logs db`

### Squid not blocking sites

- Verify Squid is running: `docker compose ps squid`
- Check ACL configuration in `squid/squid.conf`
- View proxy logs: `docker compose logs squid`

## 📖 API Documentation

### Authentication

**POST** `/api/auth/login`
```json
{
  "username": "student1",
  "password": "password123"
}
```

**POST** `/api/auth/logout`

### Configuration

**POST** `/api/config/generate`
- Requires authentication
- Returns WireGuard configuration

### Status

**GET** `/api/status`
```json
{
  "status": "online",
  "total_users": 4,
  "active_connections": 2
}
```

## 🎓 Academic Use

This project is designed for educational purposes and demonstrates:
- Modern containerization with Docker
- RESTful API design
- Database-driven authentication
- Network proxy configuration
- VPN protocol implementation (WireGuard)
- Web application development
- Cloud migration strategies

## 📄 License

MIT License - Free for academic and educational use

## 👥 Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs with `docker compose logs`
3. Check the documentation in `docs/`

## 🔐 Security Notes

**For Production Use:**
- Change all default passwords
- Use strong SECRET_KEY
- Implement proper SSL certificates (LetsEncrypt)
- Enable firewall rules
- Regular security updates
- Use environment variables for secrets
- Enable database backups

---

**Built with ❤️ for Academic Excellence**
