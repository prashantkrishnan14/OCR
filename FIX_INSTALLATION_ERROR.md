# Fix: frappe-client Dependency Error

## The Problem

When running `bench get-app https://github.com/prashantkrishnan14/OCR.git`, you get:

```
ERROR: Could not find a version that satisfies the requirement frappe-client>=0.0.2
ERROR: No matching distribution found for frappe-client>=0.0.2
```

## Why This Happens

The `frappe-client>=0.0.2` package doesn't exist in PyPI (only `0.1.0.dev0` is available). Additionally, when installing as a Frappe app, you don't need `frappe-client` at all since the app runs inside the Frappe environment and uses internal APIs.

## Solution: Quick Install (Recommended)

Use the automated installation script that handles all dependencies correctly:

```bash
cd ~/frappe-bench

# Get the updated repository
git clone https://github.com/prashantkrishnan14/OCR.git /tmp/ocr-temp
cd /tmp/ocr-temp

# Run the installation script
chmod +x install_ocr_app.sh
bash install_ocr_app.sh your-site-name

# Clean up
cd ~
rm -rf /tmp/ocr-temp
```

Replace `your-site-name` with your actual ERPNext site name.

## Solution: Manual Install

If the script doesn't work or you prefer manual installation:

### Step 1: Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr tesseract-ocr-eng poppler-utils
sudo apt-get install -y libgl1-mesa-glx libglib2.0-0
```

### Step 2: Install Python Dependencies Manually

```bash
cd ~/frappe-bench

# Install dependencies one by one
./env/bin/pip install pytesseract>=0.3.10
./env/bin/pip install Pillow>=10.0.0
./env/bin/pip install pdf2image>=1.16.3
./env/bin/pip install opencv-python-headless>=4.8.0
./env/bin/pip install python-dateutil>=2.8.2
./env/bin/pip install rapidfuzz>=3.5.2
./env/bin/pip install pandas>=2.0.0
./env/bin/pip install requests>=2.31.0
./env/bin/pip install python-dotenv>=1.0.0
```

### Step 3: Get the App (Without Installing Dependencies)

```bash
bench get-app https://github.com/prashantkrishnan14/OCR.git --skip-assets
```

Or manually clone:

```bash
cd ~/frappe-bench/apps
git clone https://github.com/prashantkrishnan14/OCR.git ocr-vendor-bill-ingestion
cd ~/frappe-bench
```

### Step 4: Install on Your Site

```bash
bench --site your-site-name install-app ocr-vendor-bill-ingestion
```

### Step 5: Restart Bench

```bash
# For development mode
bench restart

# For production mode
sudo supervisorctl restart all
```

## Verification

Check if the app is installed:

```bash
cd ~/frappe-bench
bench --site your-site-name list-apps
```

You should see `ocr-vendor-bill-ingestion` in the list.

## What Changed in the Repository

The following files have been updated to fix this issue:

1. **requirements.txt** - Removed `frappe-client` dependency
2. **requirements-standalone.txt** - NEW - For standalone usage (includes frappe-client)
3. **requirements-dev.txt** - NEW - For development environment
4. **install_ocr_app.sh** - NEW - Automated installation script
5. **INSTALLATION.md** - NEW - Comprehensive installation guide

## For Standalone Usage (Outside Frappe)

If you want to run OCR scripts outside of Frappe/ERPNext:

```bash
git clone https://github.com/prashantkrishnan14/OCR.git
cd OCR

# Install with standalone requirements
pip install -r requirements-standalone.txt

# Configure
cp .env.example .env
nano .env  # Set ERPNEXT_URL, ERPNEXT_API_KEY, etc.

# Run
python ocr_ingest.py sample_invoices/sample_invoice.pdf
```

## Troubleshooting

### Issue: Tesseract not found

```bash
sudo apt-get install tesseract-ocr
tesseract --version
```

### Issue: pdf2image error "PDFInfoNotInstalledError"

```bash
sudo apt-get install poppler-utils
pdftoppm -v
```

### Issue: OpenCV "libGL.so.1: cannot open shared object file"

```bash
sudo apt-get install libgl1-mesa-glx libglib2.0-0
```

### Issue: Permission errors

```bash
cd ~/frappe-bench
sudo chown -R $USER:$USER apps/
```

### Issue: App not appearing in site

```bash
# Manually add to apps.txt
echo "ocr-vendor-bill-ingestion" >> sites/your-site-name/apps.txt

# Migrate
bench --site your-site-name migrate

# Clear cache
bench --site your-site-name clear-cache

# Restart
bench restart
```

## Additional Resources

- [INSTALLATION.md](./INSTALLATION.md) - Complete installation guide
- [INSTALL_GUIDE.md](./INSTALL_GUIDE.md) - Frappe/ERPNext v15 installation
- [README.md](./README.md) - Project documentation
- [QUICKSTART.md](./QUICKSTART.md) - Quick start guide

## Need Help?

1. Check the logs:
   ```bash
   tail -f ~/frappe-bench/sites/your-site-name/logs/web.log
   tail -f ~/frappe-bench/sites/your-site-name/logs/worker.log
   ```

2. Open an issue on GitHub:
   https://github.com/prashantkrishnan14/OCR/issues

3. Check Frappe Forum:
   https://discuss.frappe.io/

## Summary

The key fix is to **install Python dependencies manually** before running `bench get-app` or `bench install-app`. This avoids the frappe-client version conflict and ensures all dependencies are correctly installed in the Frappe bench environment.

The easiest method is to use the provided `install_ocr_app.sh` script which handles everything automatically.
