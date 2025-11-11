# Frappe/ERPNext Version 15 Installation Guide for Ubuntu 22.04 LTS

This guide provides both automated and manual installation methods for Frappe/ERPNext version 15 on Ubuntu 22.04 LTS.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Automated Installation](#automated-installation)
- [Manual Installation](#manual-installation)
- [Post-Installation](#post-installation)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements
- **OS**: Ubuntu 22.04 LTS
- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: Minimum 20GB free space
- **User**: Non-root user with sudo privileges

### Software Requirements
The following will be installed automatically:
- Python 3.11+
- Node.js 18+
- Redis 5+
- MariaDB 10.3.x+
- Yarn 1.12+
- pip 20+
- wkhtmltopdf (version 0.12.5 with patched qt)
- NGINX (for production)

## Automated Installation

### Quick Start

1. **Download the installation script:**
   ```bash
   wget https://raw.githubusercontent.com/your-repo/install_frappe_erpnext.sh
   # OR if you have already cloned the repository
   cd OCR
   chmod +x install_frappe_erpnext.sh
   ```

2. **Make the script executable:**
   ```bash
   chmod +x install_frappe_erpnext.sh
   ```

3. **Run the installation script:**
   ```bash
   ./install_frappe_erpnext.sh [site-name]
   ```

   Example:
   ```bash
   ./install_frappe_erpnext.sh mysite.local
   ```

   If no site name is provided, it defaults to `dcode.com`

4. **Secure MariaDB (IMPORTANT):**
   After the script completes, run:
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

5. **Start the bench:**
   ```bash
   cd ~/frappe-bench
   bench start
   ```

6. **Access your site:**
   Open your browser and navigate to: `http://[site-name]:8000`

## Manual Installation

If you prefer to install step-by-step or the automated script fails, follow these manual steps:

### Step 1: Update System and Install Git
```bash
sudo apt-get update
sudo apt-get install -y git
```

### Step 2: Install Python Development Files
```bash
sudo apt-get install -y python3-dev
```

### Step 3: Install Python 3.11 (if not already installed)

**Note**: Ubuntu 23.04+ comes with Python 3.11 by default. Check your version:
```bash
python3 --version
```

If you need to install Python 3.11:
```bash
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-full
python3.11 --version
```

### Step 4: Install setuptools and pip
```bash
sudo apt-get install -y python3-setuptools python3-pip
```

### Step 5: Install virtualenv
```bash
sudo apt-get install -y python3.11-venv
```

### Step 6: Install and Configure MariaDB
```bash
sudo apt-get install -y software-properties-common
sudo apt-get install -y mariadb-server
sudo mysql_secure_installation
```

Follow the security prompts as described in the automated installation section.

### Step 7: Install MySQL Development Files
```bash
sudo apt-get install -y libmysqlclient-dev
```

### Step 8: Configure MariaDB for Unicode

Edit the MariaDB configuration:
```bash
sudo nano /etc/mysql/mariadb.conf.d/50-server.cnf
```

Replace the contents with:
```ini
[server]
user = mysql
pid-file = /run/mysqld/mysqld.pid
socket = /run/mysqld/mysqld.sock
basedir = /usr
datadir = /var/lib/mysql
tmpdir = /tmp
lc-messages-dir = /usr/share/mysql
bind-address = 127.0.0.1
query_cache_size = 16M
log_error = /var/log/mysql/error.log

[mysqld]
innodb-file-format=barracuda
innodb-file-per-table=1
innodb-large-prefix=1
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4
```

Save and restart MySQL:
```bash
sudo service mysql restart
```

### Step 9: Install Redis
```bash
sudo apt-get install -y redis-server
```

### Step 10: Install Node.js 18.x
```bash
sudo apt-get install -y curl
curl https://raw.githubusercontent.com/creationix/nvm/master/install.sh | bash
source ~/.profile
nvm install 18
```

### Step 11: Install Yarn
```bash
sudo npm install -g yarn
```

### Step 12: Install wkhtmltopdf
```bash
sudo apt-get install -y xvfb libfontconfig wkhtmltopdf
```

### Step 13: Install frappe-bench
```bash
sudo -H pip3 install frappe-bench
bench --version
```

### Step 14: Initialize Frappe Bench
```bash
cd ~
bench init frappe-bench --frappe-branch version-15 --python python3.11
cd frappe-bench/
```

### Step 15: Create a Site
```bash
bench new-site dcode.com
bench --site dcode.com add-to-hosts
```

You'll be prompted to enter:
- MySQL root password
- Administrator password for the site

### Step 16: Install ERPNext
```bash
bench get-app erpnext --branch version-15
# OR
bench get-app https://github.com/frappe/erpnext --branch version-15

bench --site dcode.com install-app erpnext
```

### Step 17: Start the Development Server
```bash
bench start
```

Access your site at: `http://dcode.com:8000`

## Post-Installation

### Starting the Bench
```bash
cd ~/frappe-bench
bench start
```

### Production Setup (Optional)

For production deployment:

1. **Install NGINX and setup production:**
   ```bash
   sudo apt-get install -y nginx
   sudo bench setup production [your-username]
   ```

2. **Enable scheduler:**
   ```bash
   bench --site [site-name] enable-scheduler
   ```

3. **Setup SSL (recommended):**
   ```bash
   sudo bench setup lets-encrypt [site-name]
   ```

### Common Bench Commands

```bash
# Start bench in development mode
bench start

# Create a new site
bench new-site [site-name]

# Install an app on a site
bench --site [site-name] install-app [app-name]

# Update bench
bench update

# Backup a site
bench --site [site-name] backup

# Restore a site
bench --site [site-name] restore [backup-file]

# Migrate a site
bench --site [site-name] migrate

# Clear cache
bench --site [site-name] clear-cache

# Clear website cache
bench --site [site-name] clear-website-cache

# Restart bench (production)
bench restart
```

## Troubleshooting

### Issue: Permission Denied Errors
**Solution**: Ensure you're not running as root. Use a normal user with sudo privileges.

### Issue: Port 8000 Already in Use
**Solution**:
```bash
# Find the process using port 8000
sudo lsof -i :8000
# Kill the process
sudo kill -9 [PID]
```

### Issue: MariaDB Connection Errors
**Solution**:
1. Ensure MariaDB is running:
   ```bash
   sudo service mysql status
   sudo service mysql restart
   ```
2. Check if you can connect:
   ```bash
   mysql -u root -p
   ```

### Issue: Node.js/NVM Not Found After Installation
**Solution**: Reload your profile or restart your terminal:
```bash
source ~/.profile
# OR
source ~/.bashrc
```

### Issue: Bench Command Not Found
**Solution**:
```bash
# Reinstall frappe-bench
sudo -H pip3 install --upgrade frappe-bench

# Add to PATH if needed
export PATH=$PATH:~/.local/bin
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
```

### Issue: wkhtmltopdf Errors
**Solution**: Install the proper patched version:
```bash
cd /tmp
wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.bionic_amd64.deb
sudo apt install -y ./wkhtmltox_0.12.6-1.bionic_amd64.deb
```

### Logs Location
- **Bench logs**: `~/frappe-bench/logs/`
- **Site logs**: `~/frappe-bench/sites/[site-name]/logs/`
- **MariaDB logs**: `/var/log/mysql/error.log`

## Additional Resources

- [Official Frappe Documentation](https://frappeframework.com/docs)
- [ERPNext Documentation](https://docs.erpnext.com/)
- [Frappe Forum](https://discuss.frappe.io/)
- [GitHub - Frappe](https://github.com/frappe/frappe)
- [GitHub - ERPNext](https://github.com/frappe/erpnext)

## Video Tutorial
- [D-codeE Video Tutorial](https://youtu.be/TReR0I0O1Xo)

## References
- [Python 3.11 Installation - LinuxCapable](https://www.linuxcapable.com/how-to-install-python-3-11-on-ubuntu-linux/)
- [Python 3.11 Installation - Ubuntu Handbook](https://ubuntuhandbook.org/index.php/2022/10/python-3-11-released-how-install-ubuntu)

## License
This guide is provided as-is for educational and installation purposes.

## Contributing
Feel free to submit issues or pull requests to improve this installation guide.
