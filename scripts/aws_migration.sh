#!/bin/bash
# AWS Migration Helper Script

echo "=========================================="
echo "AWS Migration Guide"
echo "=========================================="
echo ""
echo "This script helps prepare your VPN project for AWS deployment"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "⚠ AWS CLI is not installed"
    echo "Install it from: https://aws.amazon.com/cli/"
    echo ""
fi

echo "Migration Steps:"
echo ""
echo "1. Create ECR Repository:"
echo "   aws ecr create-repository --repository-name vpn-cloud-webui"
echo "   aws ecr create-repository --repository-name vpn-cloud-squid"
echo ""
echo "2. Login to ECR:"
echo "   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com"
echo ""
echo "3. Tag and Push Images:"
echo "   docker tag vpn-cloud-project-webui:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/vpn-cloud-webui:latest"
echo "   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/vpn-cloud-webui:latest"
echo ""
echo "4. Deploy to ECS/EC2:"
echo "   - Use AWS Console or Terraform"
echo "   - Configure security groups (ports: 51820/UDP, 443/TCP)"
echo "   - Set environment variables for production"
echo "   - Use RDS for MySQL database"
echo "   - Use ACM for SSL certificates"
echo ""
echo "For detailed instructions, see docs/aws-migration.md"
