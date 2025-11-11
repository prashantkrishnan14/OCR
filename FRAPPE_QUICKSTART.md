# Frappe/ERPNext Quick Start Guide

This repository now includes automated installation scripts for Frappe/ERPNext version 15 on Ubuntu 22.04 LTS.

## 🚀 Quick Installation

### Option 1: Full Automated Installation (Recommended)

Install everything in one go:

```bash
chmod +x install_frappe_erpnext.sh
./install_frappe_erpnext.sh [your-site-name]
```

Example:
```bash
./install_frappe_erpnext.sh mycompany.local
```

### Option 2: Step-by-Step Installation

#### Step 1: Install Dependencies Only
```bash
chmod +x install_dependencies.sh
./install_dependencies.sh
```

#### Step 2: Secure MariaDB
```bash
sudo mysql_secure_installation
```

Follow the prompts:
- Enter current password for root: **Press ENTER**
- Switch to unix_socket authentication: **Y**
- Change the root password: **Y** (set a strong password)
- Remove anonymous users: **Y**
- Disallow root login remotely: **Y**
- Remove test database: **Y**
- Reload privilege tables: **Y**

#### Step 3: Configure MariaDB
```bash
chmod +x configure_mariadb.sh
sudo ./configure_mariadb.sh
```

#### Step 4: Initialize Frappe Bench
```bash
cd ~
bench init frappe-bench --frappe-branch version-15 --python python3.11
cd frappe-bench/
```

#### Step 5: Create Site and Install ERPNext
```bash
bench new-site mysite.local
bench --site mysite.local add-to-hosts
bench get-app erpnext --branch version-15
bench --site mysite.local install-app erpnext
```

#### Step 6: Start Development Server
```bash
bench start
```

Access at: `http://mysite.local:8000`

## 📋 What Gets Installed

- ✅ Python 3.11
- ✅ Node.js 18 (via NVM)
- ✅ MariaDB Server
- ✅ Redis Server
- ✅ Yarn Package Manager
- ✅ wkhtmltopdf
- ✅ Frappe Bench
- ✅ Frappe Framework (version-15)
- ✅ ERPNext (version-15)

## 🛠️ Available Scripts

| Script | Description |
|--------|-------------|
| `install_frappe_erpnext.sh` | Complete installation of all dependencies, Frappe, and ERPNext |
| `install_dependencies.sh` | Install only system dependencies |
| `configure_mariadb.sh` | Configure MariaDB for Frappe/ERPNext |

## 📖 Documentation

For detailed installation instructions, troubleshooting, and manual installation steps, see:
- [INSTALL_GUIDE.md](./INSTALL_GUIDE.md) - Comprehensive installation guide
- [Original Guide](https://github.com/D-codE-Hub/Frappe-ERPNext-Version-15--in-Ubuntu-22.04-LTS) - Reference installation guide

## ⚡ Quick Commands

### Development Mode
```bash
cd ~/frappe-bench
bench start
```

### Common Operations
```bash
# Create a new site
bench new-site sitename.local

# Install an app
bench get-app [app-name] --branch version-15
bench --site sitename.local install-app [app-name]

# Update bench and all apps
bench update

# Backup a site
bench --site sitename.local backup

# Clear cache
bench --site sitename.local clear-cache
```

### Production Setup
```bash
# Setup production mode
sudo bench setup production $USER
bench restart

# Enable scheduler
bench --site sitename.local enable-scheduler

# Setup SSL (optional)
sudo bench setup lets-encrypt sitename.local
```

## 🐛 Troubleshooting

### MariaDB Issues
```bash
# Check MariaDB status
sudo systemctl status mysql

# Restart MariaDB
sudo systemctl restart mysql
```

### Port Already in Use
```bash
# Find process on port 8000
sudo lsof -i :8000

# Kill process
sudo kill -9 [PID]
```

### Node/NVM Not Found
```bash
# Reload profile
source ~/.profile
source ~/.bashrc
```

### Bench Command Not Found
```bash
# Add to PATH
export PATH=$PATH:~/.local/bin
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
```

## 📚 Additional Resources

- [Frappe Framework Documentation](https://frappeframework.com/docs)
- [ERPNext Documentation](https://docs.erpnext.com/)
- [Frappe Forum](https://discuss.frappe.io/)
- [Video Tutorial by D-codeE](https://youtu.be/TReR0I0O1Xo)

## 🎯 This Repository

This repository contains an OCR-based vendor bill ingestion system for ERPNext. After installing Frappe/ERPNext using the scripts above, you can integrate this OCR system with your ERPNext installation.

See [README.md](./README.md) for details about the OCR system.

## ⚠️ Requirements

- Ubuntu 22.04 LTS
- Minimum 4GB RAM (8GB recommended)
- At least 20GB free disk space
- Non-root user with sudo privileges
- Internet connection

## 🤝 Contributing

Feel free to submit issues or pull requests to improve these installation scripts.

## 📝 License

These installation scripts are provided as-is for educational purposes.
