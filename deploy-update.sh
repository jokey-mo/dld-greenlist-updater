#!/bin/bash

# Update Deployment Script
# Use this to update an already deployed application

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

echo -e "${BLUE}🔄 DLD Greenlist Updater - Update Deployment${NC}"
echo "============================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}❌ Please run this script as root (use sudo)${NC}"
    exit 1
fi

# Check if application is deployed
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}❌ Application not found at $APP_DIR${NC}"
    echo "Please run the initial deployment script first."
    exit 1
fi

echo -e "${YELLOW}📋 Update process starting...${NC}"
echo "   App Directory: $APP_DIR"
echo ""

# Backup current deployment
echo -e "${BLUE}📂 Creating backup...${NC}"
cd $APP_DIR
BACKUP_DIR="backup-$(date +%Y%m%d_%H%M%S)"
cp -r . $BACKUP_DIR
echo -e "${GREEN}✅ Backup created: $APP_DIR/$BACKUP_DIR${NC}"

# Stop the service
echo -e "${BLUE}🛑 Stopping application service...${NC}"
systemctl stop $SERVICE_NAME

# Update application files (assumes script is run from app directory)
echo -e "${BLUE}📥 Updating application files...${NC}"
if [ -f "$(dirname "$0")/app.py" ]; then
    # Copy new files, preserving instance and uploads
    cp "$(dirname "$0")"/*.py .
    cp "$(dirname "$0")/requirements.txt" .
    cp -r "$(dirname "$0")/templates" .
    
    # Update Python dependencies
    echo -e "${BLUE}📦 Updating Python dependencies...${NC}"
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo -e "${GREEN}✅ Application files updated${NC}"
else
    echo -e "${RED}❌ New application files not found.${NC}"
    echo "Please run this script from the updated application directory."
    
    # Restore from backup
    echo -e "${YELLOW}🔄 Restoring from backup...${NC}"
    rm -rf *.py templates requirements.txt
    cp -r $BACKUP_DIR/* .
    systemctl start $SERVICE_NAME
    exit 1
fi

# Set correct permissions
echo -e "${BLUE}🔐 Updating permissions...${NC}"
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR

# Start the service
echo -e "${BLUE}🚀 Starting application service...${NC}"
systemctl start $SERVICE_NAME

# Wait a moment and check status
sleep 3
if systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "${GREEN}✅ Service started successfully${NC}"
else
    echo -e "${RED}❌ Service failed to start, restoring backup...${NC}"
    systemctl stop $SERVICE_NAME
    
    # Restore from backup
    rm -rf *.py templates requirements.txt venv
    cp -r $BACKUP_DIR/* .
    
    # Restart service
    systemctl start $SERVICE_NAME
    
    echo -e "${YELLOW}⚠️  Update failed, backup restored${NC}"
    echo "Check logs: journalctl -u $SERVICE_NAME -f"
    exit 1
fi

# Cleanup old backups (keep last 5)
echo -e "${BLUE}🧹 Cleaning up old backups...${NC}"
ls -dt backup-* 2>/dev/null | tail -n +6 | xargs rm -rf 2>/dev/null || true

# Display service status
echo -e "${BLUE}📊 Service Status:${NC}"
systemctl status $SERVICE_NAME --no-pager -l

echo ""
echo -e "${GREEN}🎉 Update completed successfully!${NC}"
echo ""
echo -e "${YELLOW}📋 Update Summary:${NC}"
echo "   📂 Backup Location: $APP_DIR/$BACKUP_DIR"
echo "   📱 Service Status: $(systemctl is-active $SERVICE_NAME)"
echo "   📝 View Logs: journalctl -u $SERVICE_NAME -f"
echo ""
echo -e "${BLUE}🔍 Verification steps:${NC}"
echo "   1. Check if the application loads correctly"
echo "   2. Test login functionality"
echo "   3. Test file upload functionality"
echo "   4. Monitor logs for any errors"
echo ""
echo -e "${GREEN}✅ Application update is complete!${NC}"
