#!/bin/bash

# Simple Deployment Script (No SSH - for local/VPS setup)
# Run this script directly on your server

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

echo -e "${BLUE}🚀 DLD Greenlist Updater - Simple Deployment${NC}"
echo "============================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Please run this script as root (use sudo)${NC}"
    exit 1
fi

# Get configuration from user
read -p "🌐 Enter your domain or server IP: " DOMAIN
if [ -z "$DOMAIN" ]; then
    DOMAIN="localhost"
    echo -e "${YELLOW}⚠️  Using localhost (access via http://localhost)${NC}"
fi

read -p "🔐 Do you want to setup SSL with Let's Encrypt? [y/N]: " SETUP_SSL
SETUP_SSL=${SETUP_SSL:-n}

if [[ $SETUP_SSL =~ ^[Yy]$ ]]; then
    read -p "📧 Enter your email for SSL certificate: " EMAIL
    if [ -z "$EMAIL" ]; then
        echo -e "${RED}❌ Email is required for SSL setup${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}📋 Configuration:${NC}"
echo "   Domain/IP: $DOMAIN"
echo "   SSL Setup: $SETUP_SSL"
[ ! -z "$EMAIL" ] && echo "   Email: $EMAIL"
echo ""

# Update system
echo -e "${BLUE}📦 Updating system packages...${NC}"
apt update && apt upgrade -y

# Install required packages
echo -e "${BLUE}📦 Installing required packages...${NC}"
PACKAGES="python3 python3-pip python3-venv nginx git curl"
if [[ $SETUP_SSL =~ ^[Yy]$ ]]; then
    PACKAGES="$PACKAGES certbot python3-certbot-nginx"
fi
apt install -y $PACKAGES

# Create application directory
echo -e "${BLUE}📁 Setting up application directory...${NC}"
mkdir -p $APP_DIR
cd $APP_DIR

# Clone or copy application (assumes script is run from app directory)
echo -e "${BLUE}📥 Setting up application files...${NC}"
if [ -f "$(dirname "$0")/app.py" ]; then
    # Script is run from app directory
    cp -r "$(dirname "$0")"/* .
    # Clean up
    rm -rf .git __pycache__ *.pyc instance uploads venv .env
else
    echo -e "${RED}❌ Application files not found. Please run this script from the application directory.${NC}"
    exit 1
fi

# Create virtual environment
echo -e "${BLUE}🐍 Setting up Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${BLUE}📦 Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p instance uploads logs static

# Set permissions
echo -e "${BLUE}🔐 Setting up permissions...${NC}"
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR

# Create systemd service
echo -e "${BLUE}⚙️  Creating system service...${NC}"
cat > $SYSTEMD_SERVICE << EOF
[Unit]
Description=DLD Greenlist Updater
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
ExecStart=$APP_DIR/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create Nginx configuration
echo -e "${BLUE}🌐 Configuring Nginx...${NC}"
cat > $NGINX_CONF << EOF
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
        alias $APP_DIR/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Enable Nginx site
ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Start services
echo -e "${BLUE}🚀 Starting services...${NC}"
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME
systemctl enable nginx
systemctl reload nginx

# Setup SSL if requested
if [[ $SETUP_SSL =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}🔒 Setting up SSL certificate...${NC}"
    
    # Obtain SSL certificate
    certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email $EMAIL --redirect
    
    # Setup auto-renewal
    echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
    
    PROTOCOL="https"
else
    PROTOCOL="http"
fi

# Setup basic firewall
echo -e "${BLUE}🔥 Configuring firewall...${NC}"
ufw --force enable
ufw allow ssh
ufw allow 'Nginx Full'

# Display service status
echo -e "${BLUE}📊 Service Status:${NC}"
systemctl status $SERVICE_NAME --no-pager -l

echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo ""
echo -e "${YELLOW}📋 Deployment Summary:${NC}"
echo "   🌐 Application URL: $PROTOCOL://$DOMAIN"
echo "   📱 Service Status: systemctl status $SERVICE_NAME"
echo "   📝 Application Logs: journalctl -u $SERVICE_NAME -f"
echo "   🔧 Nginx Config: $NGINX_CONF"
if [[ $SETUP_SSL =~ ^[Yy]$ ]]; then
    echo "   🔐 SSL Certificate: Auto-renewing"
fi
echo ""
echo -e "${BLUE}🛠️  Post-deployment tasks:${NC}"
echo "   1. Visit $PROTOCOL://$DOMAIN to verify the application"
echo "   2. Register your first admin account"
echo "   3. Upload test HTML file to verify functionality"
echo ""
echo -e "${YELLOW}💡 Useful commands:${NC}"
echo "   📊 Check service: systemctl status $SERVICE_NAME"
echo "   📝 View logs: journalctl -u $SERVICE_NAME -f"
echo "   🔄 Restart app: systemctl restart $SERVICE_NAME"
echo "   🌐 Restart nginx: systemctl restart nginx"
echo ""
echo -e "${GREEN}✅ Simple deployment is ready!${NC}"
