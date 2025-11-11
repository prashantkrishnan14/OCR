#!/bin/bash

################################################################################
# OCR Vendor Bill Ingestion App Installation Script
# This script installs the OCR app into an existing Frappe/ERPNext bench
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

# Check if we're in a frappe-bench directory
if [ ! -f "sites/common_site_config.json" ]; then
    log_error "This script must be run from the frappe-bench directory"
    log_info "Usage: cd ~/frappe-bench && bash /path/to/install_ocr_app.sh [site-name]"
    exit 1
fi

# Get site name
SITE_NAME="${1}"
if [ -z "$SITE_NAME" ]; then
    log_error "Please provide a site name"
    log_info "Usage: bash install_ocr_app.sh [site-name]"
    log_info "Available sites:"
    ls -1 sites/ | grep -v "common_site_config.json" | grep -v "assets"
    exit 1
fi

# Check if site exists
if [ ! -d "sites/$SITE_NAME" ]; then
    log_error "Site '$SITE_NAME' does not exist"
    log_info "Available sites:"
    ls -1 sites/ | grep -v "common_site_config.json" | grep -v "assets"
    exit 1
fi

log_info "Installing OCR Vendor Bill Ingestion for site: $SITE_NAME"

################################################################################
# Step 1: Install System Dependencies
################################################################################
log_info "Step 1: Installing system dependencies..."

log_info "Checking for Tesseract OCR..."
if ! command -v tesseract &> /dev/null; then
    log_info "Installing Tesseract OCR..."
    sudo apt-get update
    sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
else
    log_info "Tesseract OCR already installed: $(tesseract --version | head -1)"
fi

log_info "Checking for poppler-utils..."
if ! command -v pdftoppm &> /dev/null; then
    log_info "Installing poppler-utils..."
    sudo apt-get install -y poppler-utils
else
    log_info "poppler-utils already installed"
fi

# Install OpenCV dependencies
log_info "Installing OpenCV system dependencies..."
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0 2>/dev/null || true

################################################################################
# Step 2: Get the App
################################################################################
log_info "Step 2: Getting OCR app from GitHub..."

if [ -d "apps/OCR" ] || [ -d "apps/ocr-vendor-bill-ingestion" ]; then
    log_warn "OCR app directory already exists. Updating..."
    cd apps/OCR 2>/dev/null || cd apps/ocr-vendor-bill-ingestion
    git pull
    cd ../..
else
    log_info "Cloning OCR app repository..."
    bench get-app https://github.com/prashantkrishnan14/OCR.git --skip-assets || {
        log_warn "bench get-app failed, trying manual clone..."
        cd apps
        git clone https://github.com/prashantkrishnan14/OCR.git ocr-vendor-bill-ingestion
        cd ..
    }
fi

################################################################################
# Step 3: Install Python Dependencies
################################################################################
log_info "Step 3: Installing Python dependencies..."

log_info "Installing core OCR dependencies..."
./env/bin/pip install --upgrade pip

./env/bin/pip install pytesseract>=0.3.10
./env/bin/pip install Pillow>=10.0.0
./env/bin/pip install pdf2image>=1.16.3

# Use headless version for servers
log_info "Installing OpenCV (headless version for servers)..."
./env/bin/pip uninstall -y opencv-python opencv-python-headless 2>/dev/null || true
./env/bin/pip install opencv-python-headless>=4.8.0

log_info "Installing data processing libraries..."
./env/bin/pip install python-dateutil>=2.8.2
./env/bin/pip install rapidfuzz>=3.5.2
./env/bin/pip install pandas>=2.0.0

log_info "Installing utility libraries..."
./env/bin/pip install requests>=2.31.0
./env/bin/pip install python-dotenv>=1.0.0

################################################################################
# Step 4: Install App on Site
################################################################################
log_info "Step 4: Installing app on site $SITE_NAME..."

# Determine app name
APP_NAME="ocr-vendor-bill-ingestion"
if [ -d "apps/OCR" ]; then
    APP_DIR="apps/OCR"
else
    APP_DIR="apps/ocr-vendor-bill-ingestion"
fi

log_info "Installing app from: $APP_DIR"

bench --site $SITE_NAME install-app $APP_NAME || {
    log_warn "Standard installation failed, trying alternative method..."

    # Alternative: manually add to apps.txt
    if ! grep -q "$APP_NAME" sites/$SITE_NAME/apps.txt; then
        echo "$APP_NAME" >> sites/$SITE_NAME/apps.txt
        log_info "Added $APP_NAME to apps.txt"
    fi

    # Run migrations
    bench --site $SITE_NAME migrate || log_warn "Migration may have issues, continuing..."
}

################################################################################
# Step 5: Clear Cache and Restart
################################################################################
log_info "Step 5: Clearing cache and restarting..."

bench --site $SITE_NAME clear-cache
bench --site $SITE_NAME clear-website-cache

# Build assets if needed
log_info "Building assets..."
bench build --app $APP_NAME 2>/dev/null || log_warn "Asset build skipped (may not be needed)"

# Restart
if systemctl is-active --quiet "bench-frappe-*" 2>/dev/null; then
    log_info "Restarting bench (production mode)..."
    bench restart
else
    log_warn "Bench is in development mode. Please restart manually with: bench start"
fi

################################################################################
# Installation Complete
################################################################################
log_info "=========================================="
log_info "Installation Complete!"
log_info "=========================================="
log_info ""
log_info "OCR Vendor Bill Ingestion has been installed on site: $SITE_NAME"
log_info ""
log_info "Next steps:"
log_info "1. If in development mode, restart bench:"
log_info "   bench start"
log_info ""
log_info "2. Log in to your ERPNext site: http://$SITE_NAME"
log_info ""
log_info "3. Test OCR functionality by uploading a vendor bill PDF"
log_info ""
log_info "4. Check logs if you encounter issues:"
log_info "   tail -f sites/$SITE_NAME/logs/web.log"
log_info "   tail -f sites/$SITE_NAME/logs/worker.log"
log_info ""
log_info "For troubleshooting, see: INSTALLATION.md"
log_info "=========================================="
