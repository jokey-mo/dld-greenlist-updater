#!/bin/bash

# Test script to validate deployment scripts before actual deployment
# This script checks prerequisites and validates deployment script syntax

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 DLD Greenlist Updater - Deployment Test${NC}"
echo "==========================================="

# Check if scripts exist and are executable
echo -e "${BLUE}📋 Checking deployment scripts...${NC}"

SCRIPTS=("deploy-production.sh" "deploy-simple.sh" "deploy-update.sh")
ALL_SCRIPTS_OK=true

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            echo -e "   ✅ $script (executable)"
        else
            echo -e "   ⚠️  $script (not executable) - run: chmod +x $script"
            ALL_SCRIPTS_OK=false
        fi
    else
        echo -e "   ❌ $script (missing)"
        ALL_SCRIPTS_OK=false
    fi
done

# Check bash syntax
echo -e "\n${BLUE}🔍 Validating script syntax...${NC}"
for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        if bash -n "$script" 2>/dev/null; then
            echo -e "   ✅ $script syntax OK"
        else
            echo -e "   ❌ $script syntax error"
            ALL_SCRIPTS_OK=false
        fi
    fi
done

# Check required files
echo -e "\n${BLUE}📁 Checking required files...${NC}"
REQUIRED_FILES=("app.py" "requirements.txt" "templates/" "reset_and_test.py")

for file in "${REQUIRED_FILES[@]}"; do
    if [ -e "$file" ]; then
        echo -e "   ✅ $file"
    else
        echo -e "   ❌ $file (missing)"
        ALL_SCRIPTS_OK=false
    fi
done

# Check Python dependencies
echo -e "\n${BLUE}🐍 Checking Python setup...${NC}"
if command -v python3 &> /dev/null; then
    echo -e "   ✅ Python3 available"
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    echo -e "   📋 Version: $PYTHON_VERSION"
else
    echo -e "   ❌ Python3 not found"
    ALL_SCRIPTS_OK=false
fi

if [ -f "requirements.txt" ]; then
    echo -e "   ✅ requirements.txt found"
    DEP_COUNT=$(wc -l < requirements.txt)
    echo -e "   📋 Dependencies: $DEP_COUNT"
else
    echo -e "   ❌ requirements.txt missing"
    ALL_SCRIPTS_OK=false
fi

# Environment check
echo -e "\n${BLUE}🌍 Environment recommendations...${NC}"

# Check if running in a container
if [ -f /.dockerenv ]; then
    echo -e "   ⚠️  Running in Docker container"
    echo -e "      Consider using host deployment instead"
fi

# Check available space
AVAILABLE_SPACE=$(df -h . | awk 'NR==2 {print $4}')
echo -e "   💾 Available space: $AVAILABLE_SPACE"

# Summary
echo ""
if [ "$ALL_SCRIPTS_OK" = true ]; then
    echo -e "${GREEN}🎉 All checks passed! Ready for deployment.${NC}"
    echo ""
    echo -e "${YELLOW}📋 Deployment Options:${NC}"
    echo ""
    echo -e "${BLUE}Option 1: SSH + SSL Deployment (Remote server)${NC}"
    echo "   ./deploy-production.sh <server_ip> <domain> <email>"
    echo "   Example: ./deploy-production.sh 192.168.1.100 mydomain.com admin@mydomain.com"
    echo ""
    echo -e "${BLUE}Option 2: Simple Deployment (Local/VPS)${NC}"
    echo "   sudo ./deploy-simple.sh"
    echo ""
    echo -e "${BLUE}Update Existing Deployment:${NC}"
    echo "   sudo ./deploy-update.sh"
    echo ""
    echo -e "${GREEN}✅ Choose your deployment option and proceed!${NC}"
else
    echo -e "${RED}❌ Some issues found. Please fix them before deployment.${NC}"
    echo ""
    echo -e "${YELLOW}💡 Common fixes:${NC}"
    echo "   - Make scripts executable: chmod +x deploy-*.sh"
    echo "   - Ensure all required files are present"
    echo "   - Check Python installation"
fi

echo ""
echo -e "${BLUE}🔗 For detailed instructions, see README.md${NC}"
