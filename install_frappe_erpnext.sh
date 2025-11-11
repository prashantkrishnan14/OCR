#!/bin/bash

################################################################################
# Frappe/ERPNext Version 15 Installation Script for Ubuntu 22.04 LTS
# This script automates the installation of all prerequisites and dependencies
################################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   log_error "This script should not be run as root. Please run as a normal user with sudo privileges."
   exit 1
fi

# Check Ubuntu version
log_info "Checking Ubuntu version..."
if ! grep -q "22.04" /etc/os-release; then
    log_warn "This script is designed for Ubuntu 22.04 LTS. Your version may not be compatible."
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Variables (you can modify these)
SITE_NAME="${1:-dcode.com}"
FRAPPE_VERSION="version-15"
PYTHON_VERSION="3.11"
NODE_VERSION="18"
MARIADB_ROOT_PASSWORD=""

log_info "Starting Frappe/ERPNext installation process..."
log_info "Site name: $SITE_NAME"
log_info "Frappe version: $FRAPPE_VERSION"

################################################################################
# STEP 1: Install Git
################################################################################
log_info "STEP 1: Installing Git..."
sudo apt-get update
sudo apt-get install -y git

################################################################################
# STEP 2: Install Python Development Files
################################################################################
log_info "STEP 2: Installing Python development files..."
sudo apt-get install -y python3-dev

################################################################################
# STEP 3: Install Python 3.11
################################################################################
log_info "STEP 3: Checking Python version..."
CURRENT_PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)

if [[ "$CURRENT_PYTHON_VERSION" == "3.11" ]] || [[ "$CURRENT_PYTHON_VERSION" > "3.11" ]]; then
    log_info "Python $CURRENT_PYTHON_VERSION is already installed. Skipping Python 3.11 installation."
else
    log_info "Installing Python 3.11..."
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt-get update
    sudo apt-get install -y python3.11 python3.11-full
fi

python3.11 --version

################################################################################
# STEP 4: Install setuptools and pip
################################################################################
log_info "STEP 4: Installing setuptools and pip..."
sudo apt-get install -y python3-setuptools python3-pip

################################################################################
# STEP 5: Install virtualenv
################################################################################
log_info "STEP 5: Installing virtualenv..."
sudo apt-get install -y python3.11-venv

################################################################################
# STEP 6: Install MariaDB
################################################################################
log_info "STEP 6: Installing MariaDB..."
sudo apt-get install -y software-properties-common
sudo apt-get install -y mariadb-server

log_warn "MariaDB has been installed. You will need to run mysql_secure_installation manually after this script completes."
log_warn "Please set a root password and follow the security prompts."

################################################################################
# STEP 7: Install MySQL development files
################################################################################
log_info "STEP 7: Installing MySQL database development files..."
sudo apt-get install -y libmysqlclient-dev

################################################################################
# STEP 8: Configure MariaDB
################################################################################
log_info "STEP 8: Configuring MariaDB for Frappe/ERPNext..."

# Backup original config
sudo cp /etc/mysql/mariadb.conf.d/50-server.cnf /etc/mysql/mariadb.conf.d/50-server.cnf.backup

# Create new configuration
sudo tee /etc/mysql/mariadb.conf.d/50-server.cnf > /dev/null << 'EOF'
#
# These groups are read by MariaDB server.
# Use it for options that only the server (but not clients) should see

# this is read by the standalone daemon and embedded servers
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

# this is only for the mysqld standalone daemon
[mysqld]
innodb-file-format=barracuda
innodb-file-per-table=1
innodb-large-prefix=1
character-set-client-handshake = FALSE
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# this is only for embedded server
[embedded]

# This group is only read by MariaDB servers, not by MySQL.
# If you use the same .cnf file for MySQL and MariaDB,
# you can put MariaDB-only options here
[mariadb]

# This group is only read by MariaDB-10.5 servers.
# If you use the same .cnf file for MariaDB of different versions,
# use this group for options that older servers don't understand
[mariadb-10.5]

[mysql]
default-character-set = utf8mb4
EOF

log_info "Restarting MySQL service..."
sudo service mysql restart

################################################################################
# STEP 9: Install Redis
################################################################################
log_info "STEP 9: Installing Redis..."
sudo apt-get install -y redis-server

################################################################################
# STEP 10: Install Node.js 18.x using NVM
################################################################################
log_info "STEP 10: Installing Node.js 18.x..."
sudo apt-get install -y curl

# Install NVM
if [ ! -d "$HOME/.nvm" ]; then
    log_info "Installing NVM..."
    curl -o- https://raw.githubusercontent.com/creationix/nvm/master/install.sh | bash

    # Load NVM
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
else
    log_info "NVM already installed. Loading NVM..."
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
fi

# Install Node.js 18
nvm install 18
nvm use 18

node --version
npm --version

################################################################################
# STEP 11: Install Yarn
################################################################################
log_info "STEP 11: Installing Yarn..."
sudo npm install -g yarn

yarn --version

################################################################################
# STEP 12: Install wkhtmltopdf
################################################################################
log_info "STEP 12: Installing wkhtmltopdf..."
sudo apt-get install -y xvfb libfontconfig wkhtmltopdf

################################################################################
# STEP 13: Install frappe-bench
################################################################################
log_info "STEP 13: Installing frappe-bench..."
sudo -H pip3 install frappe-bench

bench --version

################################################################################
# STEP 14: Initialize Frappe Bench
################################################################################
log_info "STEP 14: Initializing Frappe bench..."

if [ -d "$HOME/frappe-bench" ]; then
    log_warn "frappe-bench directory already exists. Skipping initialization."
else
    cd $HOME
    bench init frappe-bench --frappe-branch $FRAPPE_VERSION --python python3.11
fi

################################################################################
# STEP 15: Create Site
################################################################################
log_info "STEP 15: Creating site: $SITE_NAME..."
cd $HOME/frappe-bench

# Check if site already exists
if [ -d "$HOME/frappe-bench/sites/$SITE_NAME" ]; then
    log_warn "Site $SITE_NAME already exists. Skipping site creation."
else
    bench new-site $SITE_NAME
    bench --site $SITE_NAME add-to-hosts
fi

################################################################################
# STEP 16: Install ERPNext
################################################################################
log_info "STEP 16: Installing ERPNext..."
cd $HOME/frappe-bench

# Check if ERPNext is already installed
if [ -d "$HOME/frappe-bench/apps/erpnext" ]; then
    log_warn "ERPNext app already exists. Skipping app download."
else
    bench get-app erpnext --branch $FRAPPE_VERSION
fi

# Install ERPNext on the site
bench --site $SITE_NAME install-app erpnext

################################################################################
# Installation Complete
################################################################################
log_info "=========================================="
log_info "Installation Complete!"
log_info "=========================================="
log_info ""
log_info "Next steps:"
log_info "1. Run: cd ~/frappe-bench"
log_info "2. Run: bench start"
log_info "3. Open your browser and navigate to: http://$SITE_NAME:8000"
log_info ""
log_info "IMPORTANT: If you haven't run mysql_secure_installation yet, please do so:"
log_info "   sudo mysql_secure_installation"
log_info ""
log_info "To start the bench in development mode:"
log_info "   cd ~/frappe-bench && bench start"
log_info ""
log_info "To enable production mode (optional):"
log_info "   cd ~/frappe-bench"
log_info "   sudo bench setup production [your-user]"
log_info "   bench restart"
log_info ""
log_info "=========================================="
