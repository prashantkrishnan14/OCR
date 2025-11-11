#!/bin/bash

################################################################################
# Dependencies Installation Script for Frappe/ERPNext
# This script only installs system dependencies without setting up Frappe/ERPNext
################################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_info "Installing system dependencies for Frappe/ERPNext..."

# Update package list
log_info "Updating package list..."
sudo apt-get update

# Install basic utilities
log_info "Installing basic utilities (git, curl, software-properties-common)..."
sudo apt-get install -y git curl software-properties-common

# Install Python 3.11 and related packages
log_info "Installing Python 3.11 and development files..."
CURRENT_PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)

if [[ "$CURRENT_PYTHON_VERSION" == "3.11" ]] || [[ "$CURRENT_PYTHON_VERSION" > "3.11" ]]; then
    log_info "Python $CURRENT_PYTHON_VERSION is already installed."
else
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt-get update
    sudo apt-get install -y python3.11 python3.11-full
fi

sudo apt-get install -y python3-dev python3-setuptools python3-pip python3.11-venv

# Install MariaDB
log_info "Installing MariaDB server..."
sudo apt-get install -y mariadb-server libmysqlclient-dev

# Install Redis
log_info "Installing Redis server..."
sudo apt-get install -y redis-server

# Install Node.js dependencies
log_info "Installing Node.js via NVM..."
if [ ! -d "$HOME/.nvm" ]; then
    curl -o- https://raw.githubusercontent.com/creationix/nvm/master/install.sh | bash
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    nvm install 18
    nvm use 18
else
    log_info "NVM already installed."
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    nvm install 18
    nvm use 18
fi

# Install Yarn
log_info "Installing Yarn..."
sudo npm install -g yarn

# Install wkhtmltopdf
log_info "Installing wkhtmltopdf..."
sudo apt-get install -y xvfb libfontconfig wkhtmltopdf

# Install frappe-bench
log_info "Installing frappe-bench..."
sudo -H pip3 install frappe-bench

log_info "=========================================="
log_info "All dependencies installed successfully!"
log_info "=========================================="
log_info ""
log_info "Next steps:"
log_info "1. Secure MariaDB: sudo mysql_secure_installation"
log_info "2. Configure MariaDB for Frappe (see INSTALL_GUIDE.md)"
log_info "3. Run the full installation script or follow manual setup"
log_info ""
