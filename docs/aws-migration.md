# AWS Migration Guide

## Overview

This guide walks you through migrating your VPN Cloud Project from local Docker development to AWS cloud infrastructure.

## AWS Architecture

### Recommended Setup (Free Tier Compatible)

```
Internet
    │
    ├─→ Route 53 (DNS)
    │
    ├─→ Application Load Balancer (ALB)
    │
    ├─→ EC2 Instance (t2.micro) - Web UI + WireGuard
    │
    ├─→ RDS MySQL (db.t2.micro) - User Database
    │
    └─→ CloudWatch Logs
```

### Services Used

| Service | Free Tier | Purpose |
|---------|-----------|---------|
| EC2 t2.micro | 750 hrs/month | VPN server + Web UI |
| RDS db.t2.micro | 750 hrs/month | MySQL database |
| EBS Storage | 30 GB | Persistent storage |
| ALB | 750 hrs/month | Load balancing + SSL |
| CloudWatch | 10 metrics | Monitoring |

## Pre-Migration Checklist

- [ ] AWS account created
- [ ] AWS CLI installed and configured
- [ ] Docker images built and tested locally
- [ ] Domain name registered (optional)
- [ ] AWS key pair created for SSH access

## Step-by-Step Migration

### 1. Create ECR Repositories

```bash
# Login to AWS
aws configure

# Create repositories for your images
aws ecr create-repository --repository-name vpn-webui --region us-east-1
aws ecr create-repository --repository-name vpn-squid --region us-east-1

# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

### 2. Build and Push Images

```bash
# Build images
docker compose build

# Tag images
docker tag vpn-cloud-project-webui:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/vpn-webui:latest
docker tag vpn-cloud-project-squid:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/vpn-squid:latest

# Push to ECR
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/vpn-webui:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/vpn-squid:latest
```

### 3. Create VPC and Security Groups

```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=vpn-vpc}]'

# Create security group for VPN server
aws ec2 create-security-group --group-name vpn-server-sg --description "VPN Server Security Group" --vpc-id <vpc-id>

# Add inbound rules
aws ec2 authorize-security-group-ingress --group-id <sg-id> --protocol udp --port 51820 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id <sg-id> --protocol tcp --port 443 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id <sg-id> --protocol tcp --port 22 --cidr <your-ip>/32
```

### 4. Launch RDS MySQL Instance

```bash
aws rds create-db-instance \
    --db-instance-identifier vpn-database \
    --db-instance-class db.t2.micro \
    --engine mysql \
    --master-username admin \
    --master-user-password <secure-password> \
    --allocated-storage 20 \
    --vpc-security-group-ids <db-sg-id> \
    --publicly-accessible
```

Wait for RDS instance to be available, then load the schema:

```bash
mysql -h <rds-endpoint> -u admin -p < db/init.sql
```

### 5. Launch EC2 Instance

Create user data script (`user-data.sh`):

```bash
#!/bin/bash
# Install Docker
apt-get update
apt-get install -y docker.io docker-compose

# Pull and run containers
docker pull <account-id>.dkr.ecr.us-east-1.amazonaws.com/vpn-webui:latest
docker pull <account-id>.dkr.ecr.us-east-1.amazonaws.com/vpn-squid:latest
docker pull linuxserver/wireguard:latest

# Create docker-compose file
cat > /home/ubuntu/docker-compose.yml << 'EOF'
version: '3.8'
services:
  wireguard:
    image: linuxserver/wireguard:latest
    # ... (same config as local)

  webui:
    image: <account-id>.dkr.ecr.us-east-1.amazonaws.com/vpn-webui:latest
    environment:
      DB_HOST: <rds-endpoint>
      DB_USER: admin
      DB_PASSWORD: <secure-password>

  squid:
    image: <account-id>.dkr.ecr.us-east-1.amazonaws.com/vpn-squid:latest
EOF

# Start services
cd /home/ubuntu
docker-compose up -d
```

Launch the instance:

```bash
aws ec2 run-instances \
    --image-id ami-0c55b159cbfafe1f0 \  # Ubuntu 20.04 LTS
    --instance-type t2.micro \
    --key-name your-key-pair \
    --security-group-ids <sg-id> \
    --user-data file://user-data.sh \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=vpn-server}]'
```

### 6. Configure SSL with ACM

```bash
# Request certificate (requires domain verification)
aws acm request-certificate \
    --domain-name vpn.yourdomain.com \
    --validation-method DNS
```

### 7. Create Application Load Balancer

```bash
# Create ALB
aws elbv2 create-load-balancer \
    --name vpn-alb \
    --subnets <subnet-1> <subnet-2> \
    --security-groups <alb-sg-id> \
    --scheme internet-facing

# Create target group
aws elbv2 create-target-group \
    --name vpn-targets \
    --protocol HTTPS \
    --port 443 \
    --vpc-id <vpc-id>

# Register EC2 instance
aws elbv2 register-targets \
    --target-group-arn <tg-arn> \
    --targets Id=<instance-id>

# Create listener with ACM certificate
aws elbv2 create-listener \
    --load-balancer-arn <alb-arn> \
    --protocol HTTPS \
    --port 443 \
    --certificates CertificateArn=<acm-cert-arn> \
    --default-actions Type=forward,TargetGroupArn=<tg-arn>
```

### 8. Configure Route 53 (Optional)

```bash
# Create hosted zone
aws route53 create-hosted-zone --name yourdomain.com --caller-reference $(date +%s)

# Create A record pointing to ALB
aws route53 change-resource-record-sets \
    --hosted-zone-id <zone-id> \
    --change-batch file://dns-record.json
```

`dns-record.json`:
```json
{
  "Changes": [{
    "Action": "CREATE",
    "ResourceRecordSet": {
      "Name": "vpn.yourdomain.com",
      "Type": "A",
      "AliasTarget": {
        "HostedZoneId": "<alb-hosted-zone>",
        "DNSName": "<alb-dns-name>",
        "EvaluateTargetHealth": false
      }
    }
  }]
}
```

## Alternative: ECS Deployment

For a more managed approach, use ECS Fargate:

### 1. Create ECS Cluster

```bash
aws ecs create-cluster --cluster-name vpn-cluster
```

### 2. Create Task Definition

```json
{
  "family": "vpn-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "webui",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/vpn-webui:latest",
      "portMappings": [{"containerPort": 5000}],
      "environment": [
        {"name": "DB_HOST", "value": "<rds-endpoint>"}
      ]
    }
  ]
}
```

### 3. Create Service

```bash
aws ecs create-service \
    --cluster vpn-cluster \
    --service-name vpn-service \
    --task-definition vpn-task \
    --desired-count 1 \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={subnets=[<subnet-id>],securityGroups=[<sg-id>],assignPublicIp=ENABLED}"
```

## Cost Estimation

### Free Tier (First 12 Months)

- **EC2 t2.micro**: 750 hours/month = $0
- **RDS db.t2.micro**: 750 hours/month = $0
- **EBS 30GB**: Free tier = $0
- **ALB**: 750 hours/month = $0
- **Data Transfer**: 15 GB/month = $0

**Total: $0/month** (within free tier limits)

### After Free Tier

- **EC2 t2.micro**: ~$10/month
- **RDS db.t2.micro**: ~$15/month
- **EBS 30GB**: ~$3/month
- **ALB**: ~$20/month
- **Data Transfer**: ~$0.09/GB

**Total: ~$50-60/month**

## Monitoring and Maintenance

### CloudWatch Alarms

```bash
# CPU alarm
aws cloudwatch put-metric-alarm \
    --alarm-name vpn-high-cpu \
    --alarm-description "Alert when CPU exceeds 80%" \
    --metric-name CPUUtilization \
    --namespace AWS/EC2 \
    --statistic Average \
    --period 300 \
    --threshold 80 \
    --comparison-operator GreaterThanThreshold
```

### Backup Strategy

1. **Database**: RDS automated backups (enabled by default)
2. **Configuration**: Store in S3 or Git
3. **EBS Snapshots**: Weekly automated snapshots

## Security Hardening

- [ ] Enable AWS WAF on ALB
- [ ] Implement VPC Flow Logs
- [ ] Enable GuardDuty for threat detection
- [ ] Use AWS Secrets Manager for credentials
- [ ] Enable MFA for AWS account
- [ ] Implement least-privilege IAM policies
- [ ] Regular security patches via Systems Manager

## Rollback Plan

If migration fails:

1. Keep local environment running
2. Terminate AWS resources
3. Delete ECR images if needed
4. No data loss (RDS snapshots available)

## Post-Migration Checklist

- [ ] All services running and healthy
- [ ] SSL certificate valid
- [ ] DNS resolving correctly
- [ ] VPN connections working
- [ ] YouTube restriction enforced
- [ ] Database accessible
- [ ] Monitoring alerts configured
- [ ] Backup strategy implemented
- [ ] Documentation updated with AWS endpoints

## Support

For AWS-specific issues:
- AWS Support (free tier includes basic support)
- AWS Documentation: https://docs.aws.amazon.com
- AWS Forums: https://forums.aws.amazon.com

---

**Remember to clean up unused resources to avoid charges!**
