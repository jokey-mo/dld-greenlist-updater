# DLD Greenlist Updater

A Python web application for parsing and managing Dubai Land Department (DLD) client greenlist data from HTML files. The service automatically detects new clients, provides user authentication, advanced filtering, and sorting capabilities with a web interface for tracking changes over time.

## ✨ Features

- � **Multi-User Support**: Secure user authentication with data isolation
- �📊 **HTML Parsing**: Automatically extracts client information from saved HTML files
- 🔍 **Smart Duplicate Detection**: Hash-based comparison with in-file duplicate handling
- 📈 **Change Tracking**: Highlights new clients from each upload
- 🌐 **Modern Web Interface**: Clean, responsive Bootstrap UI
- � **Advanced Search & Filter**: Search by name, email, phone, area with service category and status filters
- � **Sortable Columns**: Click column headers to sort data
- 📄 **Excel Export**: Export filtered data to Excel format with current filters applied
- 📅 **Date Intelligence**: Proper date parsing and sorting for subscription end dates
- 🔐 **Secure Authentication**: Password hashing with bcrypt
- 📱 **Responsive Design**: Works on desktop and mobile devices

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Local Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd dld-greenlist-updater
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python app.py
   ```

4. **Access the web interface**:
   Open your browser and go to: `http://localhost:5000`

5. **First-time setup**:
   - Register a new account
   - Upload your first HTML file
   - Start managing your client data!

## 📚 Usage Guide

### Getting HTML Files

1. Visit the Dubai Land Department website
2. Navigate to the "Owners Green List" page
3. Save the complete webpage as HTML (Ctrl+S / Cmd+S)
4. Choose "Complete Web Page" format

### Application Features

- **🏠 Dashboard**: Overview with client counts and statistics
- **📋 All Clients**: Complete list with advanced filtering and sorting
- **⭐ New Clients**: Recently added clients from latest upload
- **📤 Upload**: Process new HTML files
- **📊 Export**: Download filtered data as Excel
- **🔐 Authentication**: Secure login/logout

### Filtering & Sorting

- **Search**: Text search across name, email, phone, area
- **Service Category**: Multi-select filter (Lease Property, Sell Property, etc.)
- **Status**: Filter by New/Existing clients
- **Sorting**: Click any column header to sort
- **Export**: Downloads respect current filters and sorting

## 🌐 Production Deployment

We provide **two automated deployment options**:

### Option 1: SSH + SSL Deployment (Recommended)

**Best for**: Remote server deployment with automatic SSL setup

```bash
./deploy-production.sh <server_ip> <domain> <email>
```

**Example**:
```bash
./deploy-production.sh 192.168.1.100 mydomain.com admin@mydomain.com
```

**Features**:
- ✅ Automatic SSL certificate with Let's Encrypt
- ✅ Nginx reverse proxy configuration
- ✅ Systemd service setup
- ✅ Firewall configuration
- ✅ Auto-renewal for SSL certificates
- ✅ Production-ready security settings

**Requirements**:
- Root SSH access to target server
- Domain pointing to server IP
- Ubuntu/Debian server

### Option 2: Simple Local Deployment

**Best for**: VPS where you have direct access, local servers

```bash
sudo ./deploy-simple.sh
```

**Features**:
- ✅ Interactive setup process
- ✅ Optional SSL with Let's Encrypt
- ✅ Nginx configuration
- ✅ Systemd service
- ✅ Basic firewall setup
- ✅ Runs directly on target server

**Requirements**:
- Run directly on target server
- Root/sudo access
- Ubuntu/Debian system

### 🔄 Updating Deployments

For both deployment options, use the update script:

```bash
sudo ./deploy-update.sh
```

**Features**:
- ✅ Automatic backup before update
- ✅ Zero-downtime deployment
- ✅ Automatic rollback on failure
- ✅ Service health checking

## 📋 Deployment Details

### What Gets Installed

Both deployment scripts set up:

- **Python 3** with virtual environment
- **Nginx** as reverse proxy
- **Systemd service** for auto-start
- **UFW firewall** with proper rules
- **SSL certificates** (if requested)
- **Cron jobs** for certificate renewal

### File Structure (Production)

```
/var/www/dld-greenlist-updater/
├── app.py                    # Main application
├── requirements.txt          # Dependencies
├── templates/               # HTML templates
├── venv/                   # Python virtual environment
├── instance/               # Database directory
├── uploads/               # Uploaded HTML files
├── logs/                 # Application logs
└── backup-*/            # Automatic backups
```

### Service Management

```bash
# Check service status
sudo systemctl status dld-greenlist

# View logs
sudo journalctl -u dld-greenlist -f

# Restart service
sudo systemctl restart dld-greenlist

# Restart Nginx
sudo systemctl restart nginx
```

### Configuration Files

- **Systemd Service**: `/etc/systemd/system/dld-greenlist.service`
- **Nginx Config**: `/etc/nginx/sites-available/dld-greenlist-updater`
- **Application**: `/var/www/dld-greenlist-updater/`

## 🗃️ Database Schema

**Users Table**:
- `id`, `name`, `email`, `password_hash`, `created_at`

**Clients Table** (per user):
- `id`, `user_id` (foreign key), `name`, `service_category`
- `property_type`, `area`, `budget`, `email`, `phone`
- `subscription_end_date`, `data_hash`, `created_at`, `updated_at`, `is_new`

## 🔧 Configuration

### Environment Variables (.env.production)

```bash
FLASK_ENV=production
SECRET_KEY=your-super-secret-key
DATABASE_URL=sqlite:///instance/clients.db
SESSION_COOKIE_SECURE=True
MAX_CONTENT_LENGTH=52428800
```

### Security Features

- 🔐 **Password Hashing**: bcrypt with salt
- 🍪 **Secure Sessions**: HTTPOnly, Secure cookies
- 🔒 **Data Isolation**: Complete user separation
- 🛡️ **Input Validation**: Form validation and sanitization
- 🚫 **CSRF Protection**: Flask-WTF CSRF tokens

## 🛠️ Development

### Local Development Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run in development mode
FLASK_ENV=development python app.py

# Reset data for testing
python reset_and_test.py
```

### Testing

```bash
# Test HTML parser
python test_parser.py

# Reset application data
python reset_and_test.py
```

## 🐳 Docker Deployment (Alternative)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "app.py"]
```

```bash
# Build and run
docker build -t dld-greenlist-updater .
docker run -p 5000:5000 -v $(pwd)/instance:/app/instance dld-greenlist-updater
```

## 🔍 Troubleshooting

### Common Issues

**Authentication Problems**:
```bash
# Check if email_validator is installed
pip install email_validator
```

**File Upload Issues**:
```bash
# Check upload directory permissions
sudo chown -R www-data:www-data /var/www/dld-greenlist-updater
```

**Database Issues**:
```bash
# Reset database
python reset_and_test.py
```

**SSL Certificate Issues**:
```bash
# Renew SSL certificate
sudo certbot renew
```

### Debug Mode

```bash
# Local debugging
FLASK_ENV=development python app.py

# Check logs
sudo journalctl -u dld-greenlist -f
```

## 📞 Support

1. **Documentation**: Check this README first
2. **Logs**: Use `journalctl -u dld-greenlist -f` for issues
3. **Reset**: Use `reset_and_test.py` for fresh start
4. **Updates**: Use `deploy-update.sh` for zero-downtime updates

## 📄 License

This project is open source. See LICENSE file for details.

---

**🎯 Ready to deploy?** Choose your deployment option and get started in minutes!
