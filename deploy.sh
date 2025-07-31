#!/bin/bash

# DLD Greenlist Updater Deployment Script

echo "🚀 Starting DLD Greenlist Updater deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check Python version
print_info "Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+')
required_version="3.8.0"

if python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
    print_status "Python version $python_version is compatible"
else
    print_error "Python 3.8+ is required. Current version: $python_version"
    exit 1
fi

# Check if pip is available
if command -v pip3 &> /dev/null; then
    print_status "pip3 is available"
else
    print_error "pip3 is not installed"
    exit 1
fi

# Install Python dependencies
print_info "Installing Python dependencies..."
if pip3 install -r requirements.txt; then
    print_status "Dependencies installed successfully"
else
    print_error "Failed to install dependencies"
    exit 1
fi

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p uploads
mkdir -p logs
print_status "Directories created"

# Initialize database if it doesn't exist
if [ ! -f "brokers.db" ]; then
    print_info "Initializing database..."
    if python3 init_db.py; then
        print_status "Database initialized successfully"
    else
        print_error "Failed to initialize database"
        exit 1
    fi
else
    print_warning "Database already exists, skipping initialization"
fi

# Set appropriate permissions
print_info "Setting file permissions..."
chmod +x *.py
chmod 755 uploads
print_status "Permissions set"

# Create systemd service file (for production deployment)
print_info "Creating systemd service file..."
cat > dld-greenlist-updater.service << EOF
[Unit]
Description=DLD Greenlist Updater
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(which python3) app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF
print_status "Systemd service file created: dld-greenlist-updater.service"

# Display deployment information
echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. To start the application locally:"
echo "   python3 app.py"
echo ""
echo "2. To run in production with systemd:"
echo "   sudo cp dld-greenlist-updater.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable dld-greenlist-updater"
echo "   sudo systemctl start dld-greenlist-updater"
echo ""
echo "3. To run with Docker:"
echo "   docker-compose up -d"
echo ""
echo "4. Access the web interface at:"
echo "   http://localhost:5000"
echo ""
echo "📊 Current status:"
if [ -f "brokers.db" ]; then
    broker_count=$(python3 -c "
from app import app, Broker
with app.app_context():
    print(Broker.query.count())
" 2>/dev/null)
    if [ ! -z "$broker_count" ]; then
        echo "   Database contains $broker_count brokers"
    fi
fi

echo ""
print_info "For more information, see README.md"
