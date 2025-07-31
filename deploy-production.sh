#!/bin/bash

# Production Deployment Script with SSL (SSH + Certbot)
# This script sets up the application on a remote server with SSL certificate

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="dld-greenlist-updater"
APP_DIR="/var/www/$APP_NAME"
SERVICE_NAME="dld-greenlist"
NGINX_CONF="/etc/nginx/sites-available/$APP_NAME"
SYSTEMD_SERVICE="/etc/systemd/system/$SERVICE_NAME.service"

echo -e "${BLUE}🚀 DLD Greenlist Updater - Production Deployment${NC}"
echo "================================================="

# Check if required parameters are provided
if [ $# -lt 3 ]; then
    echo -e "${RED}❌ Usage: $0 <server_ip> <domain> <email>${NC}"
    echo "Example: $0 192.168.1.100 mydomain.com admin@mydomain.com"
    exit 1
fi

SERVER_IP="$1"
DOMAIN="$2"
EMAIL="$3"

echo -e "${YELLOW}📋 Configuration:${NC}"
echo "   Server IP: $SERVER_IP"
echo "   Domain: $DOMAIN"
echo "   Email: $EMAIL"
echo ""

# Test SSH connection
echo -e "${BLUE}🔐 Testing SSH connection...${NC}"
if ! ssh -o ConnectTimeout=10 -o BatchMode=yes root@$SERVER_IP exit 2>/dev/null; then
    echo -e "${RED}❌ Cannot connect to server via SSH${NC}"
    echo "Please ensure:"
    echo "  1. SSH key is set up for root@$SERVER_IP"
    echo "  2. Server is accessible"
    echo "  3. You have root access"
    exit 1
fi
echo -e "${GREEN}✅ SSH connection successful${NC}"

# Create deployment package
echo -e "${BLUE}📦 Creating deployment package...${NC}"
tar -czf dld-deployment.tar.gz \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='instance' \
    --exclude='uploads' \
    --exclude='*.tar.gz' \
    --exclude='venv' \
    --exclude='.env' \
    .

echo -e "${GREEN}✅ Deployment package created${NC}"

# Upload and deploy
echo -e "${BLUE}🌐 Deploying to server...${NC}"

ssh root@$SERVER_IP << EOF
set -e

echo "📥 Preparing server environment..."

# Update system
apt update && apt upgrade -y

# Install required packages
apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx supervisor git

# Create application directory
mkdir -p $APP_DIR
cd $APP_DIR

# Backup existing deployment if it exists
if [ -d "current" ]; then
    echo "📂 Backing up current deployment..."
    mv current backup-\$(date +%Y%m%d_%H%M%S) || true
fi

mkdir -p current
EOF

# Upload application files
echo -e "${BLUE}📤 Uploading application files...${NC}"
scp dld-deployment.tar.gz root@$SERVER_IP:$APP_DIR/
rm dld-deployment.tar.gz

ssh root@$SERVER_IP << EOF
set -e
cd $APP_DIR

# Extract application
tar -xzf dld-deployment.tar.gz -C current/
rm dld-deployment.tar.gz

cd current

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p instance uploads logs

# Set permissions
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR

echo "🔧 Setting up system services..."

# Create systemd service
cat > $SYSTEMD_SERVICE << 'SERVICE_EOF'
[Unit]
Description=DLD Greenlist Updater
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR/current
Environment=PATH=$APP_DIR/current/venv/bin
ExecStart=$APP_DIR/current/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE_EOF

# Create Nginx configuration
cat > $NGINX_CONF << 'NGINX_EOF'
server {
    listen 80;
    server_name $DOMAIN;

    client_max_body_size 50M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static {
        alias $APP_DIR/current/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
NGINX_EOF

# Enable Nginx site
ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Start services
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME
systemctl reload nginx

echo "🔒 Setting up SSL certificate..."

# Obtain SSL certificate
certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL --redirect

# Setup auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -

echo "🔥 Setting up firewall..."

# Configure UFW firewall
ufw --force enable
ufw allow ssh
ufw allow 'Nginx Full'

systemctl status $SERVICE_NAME --no-pager -l

EOF

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo -e "${YELLOW}📋 Deployment Summary:${NC}"
echo "   🌐 Application URL: https://$DOMAIN"
echo "   📱 Service Status: systemctl status $SERVICE_NAME"
echo "   📝 Application Logs: journalctl -u $SERVICE_NAME -f"
echo "   🔧 Nginx Config: $NGINX_CONF"
echo "   🔐 SSL Certificate: Auto-renewing"
echo ""
echo -e "${BLUE}🛠️  Post-deployment tasks:${NC}"
echo "   1. Visit https://$DOMAIN to verify the application"
echo "   2. Register your first admin account"
echo "   3. Upload test HTML file to verify functionality"
echo ""
echo -e "${GREEN}✅ Production deployment with SSL is ready!${NC}"
