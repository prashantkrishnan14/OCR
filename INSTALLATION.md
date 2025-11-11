# OCR Vendor Bill Ingestion - Installation Guide

This guide covers installing the OCR Vendor Bill Ingestion app for ERPNext.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation Methods](#installation-methods)
- [System Dependencies](#system-dependencies)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### 1. Frappe/ERPNext Installation
This app requires a working Frappe/ERPNext installation. See [INSTALL_GUIDE.md](./INSTALL_GUIDE.md) for Frappe/ERPNext setup.

### 2. System Dependencies

Install Tesseract OCR and poppler-utils:

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y tesseract-ocr poppler-utils

# For better OCR accuracy, install additional language packs
sudo apt-get install -y tesseract-ocr-eng tesseract-ocr-deu tesseract-ocr-fra
```

## Installation Methods

### Method 1: Install as Frappe App (Recommended)

This is the recommended method when you have ERPNext already installed.

```bash
# Navigate to your frappe-bench directory
cd ~/frappe-bench

# Get the app from GitHub
bench get-app https://github.com/prashantkrishnan14/OCR.git

# Install the app on your site
bench --site your-site-name install-app ocr-vendor-bill-ingestion

# Restart bench
bench restart
```

**If you get dependency errors**, follow these steps:

1. **First, install system dependencies:**
   ```bash
   sudo apt-get install -y tesseract-ocr poppler-utils
   ```

2. **Then install the app without dependencies:**
   ```bash
   cd ~/frappe-bench
   bench get-app https://github.com/prashantkrishnan14/OCR.git --skip-assets

   # Install Python dependencies manually
   ./env/bin/pip install pytesseract Pillow pdf2image opencv-python-headless
   ./env/bin/pip install python-dateutil rapidfuzz pandas

   # Now install the app on your site
   bench --site your-site-name install-app ocr-vendor-bill-ingestion
   bench restart
   ```

### Method 2: Manual Installation

If you want more control over the installation:

```bash
# 1. Navigate to frappe-bench apps directory
cd ~/frappe-bench/apps

# 2. Clone the repository
git clone https://github.com/prashantkrishnan14/OCR.git ocr-vendor-bill-ingestion

# 3. Install system dependencies
sudo apt-get install -y tesseract-ocr poppler-utils

# 4. Install Python dependencies (minimal set)
cd ~/frappe-bench
./env/bin/pip install pytesseract Pillow pdf2image opencv-python-headless
./env/bin/pip install python-dateutil rapidfuzz pandas requests

# 5. Install the app
bench --site your-site-name install-app ocr-vendor-bill-ingestion

# 6. Restart
bench restart
```

### Method 3: Standalone Usage (Outside Frappe)

If you want to use the OCR scripts standalone (without ERPNext):

```bash
# 1. Clone the repository
git clone https://github.com/prashantkrishnan14/OCR.git
cd OCR

# 2. Install system dependencies
sudo apt-get install -y tesseract-ocr poppler-utils python3-pip

# 3. Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# 4. Install Python dependencies
pip install -r requirements-standalone.txt

# 5. Configure environment
cp .env.example .env
nano .env  # Edit with your ERPNext URL and API credentials

# 6. Run the OCR script
python ocr_ingest.py sample_invoices/sample_invoice.pdf
```

## System Dependencies Explained

### Tesseract OCR
Required for optical character recognition.

```bash
# Check if installed
tesseract --version

# Install on Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Install additional languages (optional)
sudo apt-get install tesseract-ocr-eng  # English
sudo apt-get install tesseract-ocr-deu  # German
sudo apt-get install tesseract-ocr-fra  # French
```

### Poppler Utils
Required for PDF to image conversion.

```bash
# Check if installed
pdftoppm -v

# Install on Ubuntu/Debian
sudo apt-get install poppler-utils
```

### OpenCV Dependencies
If you get OpenCV errors:

```bash
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0
```

## Configuration

### For Frappe App Installation

The app uses Frappe's internal APIs, no additional configuration needed.

### For Standalone Usage

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your settings:**
   ```bash
   nano .env
   ```

3. **Required settings:**
   ```ini
   # ERPNext API Settings
   ERPNEXT_URL=https://your-erpnext-site.com
   ERPNEXT_API_KEY=your-api-key
   ERPNEXT_API_SECRET=your-api-secret

   # OCR Settings
   OCR_ENGINE=tesseract
   ```

## Verification

### Test the Installation

1. **Check if the app is installed:**
   ```bash
   cd ~/frappe-bench
   bench --site your-site-name list-apps
   ```

2. **Test OCR functionality:**
   ```bash
   # In bench console
   bench --site your-site-name console

   # In Python console
   >>> import pytesseract
   >>> print(pytesseract.get_tesseract_version())
   ```

3. **Test with a sample invoice:**
   - Upload a vendor bill PDF through ERPNext UI
   - Check if OCR processing works

## Troubleshooting

### Error: "Could not find a version that satisfies the requirement frappe-client"

**Solution**: Use the fixed requirements file or install manually:
```bash
cd ~/frappe-bench
./env/bin/pip install pytesseract Pillow pdf2image opencv-python-headless python-dateutil rapidfuzz pandas
bench --site your-site-name install-app ocr-vendor-bill-ingestion
```

### Error: "TesseractNotFoundError"

**Solution**: Install Tesseract:
```bash
sudo apt-get install tesseract-ocr
tesseract --version
```

### Error: "pdf2image exceptions.PDFInfoNotInstalledError"

**Solution**: Install poppler-utils:
```bash
sudo apt-get install poppler-utils
```

### Error: "ImportError: libGL.so.1"

**Solution**: Install OpenCV dependencies:
```bash
sudo apt-get install libgl1-mesa-glx libglib2.0-0
```

### Error: "Module 'cv2' has no attribute 'imread'"

**Solution**: Reinstall opencv-python:
```bash
cd ~/frappe-bench
./env/bin/pip uninstall opencv-python opencv-python-headless -y
./env/bin/pip install opencv-python-headless
```

### App Installation Hangs

**Solution**: Install without assets:
```bash
bench get-app https://github.com/prashantkrishnan14/OCR.git --skip-assets
./env/bin/pip install pytesseract Pillow pdf2image opencv-python-headless python-dateutil rapidfuzz pandas
bench --site your-site-name install-app ocr-vendor-bill-ingestion
```

### Permission Errors

**Solution**: Ensure correct ownership:
```bash
cd ~/frappe-bench
sudo chown -R $USER:$USER apps/ocr-vendor-bill-ingestion
```

## Updating the App

```bash
cd ~/frappe-bench
bench update --app ocr-vendor-bill-ingestion
bench --site your-site-name migrate
bench restart
```

## Uninstalling the App

```bash
cd ~/frappe-bench
bench --site your-site-name uninstall-app ocr-vendor-bill-ingestion
bench remove-app ocr-vendor-bill-ingestion
```

## Additional Resources

- [Project README](./README.md)
- [Frappe/ERPNext Installation Guide](./INSTALL_GUIDE.md)
- [Quick Start Guide](./QUICKSTART.md)
- [Architecture Documentation](./ARCHITECTURE.md)

## Support

For issues and questions:
- Check the [Troubleshooting](#troubleshooting) section above
- Review [GitHub Issues](https://github.com/prashantkrishnan14/OCR/issues)
- Consult [Frappe Forum](https://discuss.frappe.io/)

## Notes

- **opencv-python-headless** is used instead of **opencv-python** to avoid GUI dependencies on servers
- Google Vision API is optional and only needed if you want cloud-based OCR
- Testing dependencies (pytest, etc.) are optional and only needed for development
