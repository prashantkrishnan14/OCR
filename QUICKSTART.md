# Quick Start Guide

Get up and running with OCR Vendor Bill Ingestion in 5 minutes!

## Prerequisites

- Python 3.10 or higher
- Tesseract OCR installed
- ERPNext instance with API access

## Installation (5 steps)

### 1. Install Tesseract

**Ubuntu/Debian:**
```bash
sudo apt-get update && sudo apt-get install -y tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

### 2. Clone and Install

```bash
git clone <repository-url>
cd OCR
pip install -r requirements.txt
```

### 3. Configure

```bash
cp .env.example .env
```

Edit `.env`:
```env
ERPNEXT_URL=https://your-erpnext.com
ERPNEXT_API_KEY=your_key_here
ERPNEXT_API_SECRET=your_secret_here
```

### 4. Get ERPNext API Keys

1. Log into ERPNext
2. Go to: User → Your User → API Access
3. Click "Generate Keys"
4. Copy API Key and API Secret to `.env`

### 5. Test Installation

```bash
# Test without ERPNext (extraction only)
python demo_extract_only.py sample_invoices/sample_invoice.txt

# Test with ERPNext (full flow)
python ocr_ingest.py --file your_invoice.pdf
```

## Basic Usage

### Extract data only (no ERPNext)
```bash
python demo_extract_only.py invoice.pdf
```

### Create Purchase Invoice in ERPNext
```bash
python ocr_ingest.py --file invoice.pdf
```

### Save result to file
```bash
python ocr_ingest.py --file invoice.pdf --output result.json --pretty
```

## Common Commands

```bash
# Process with custom credentials
python ocr_ingest.py --file invoice.pdf \
  --erp-url https://erp.example.com \
  --api-key KEY --api-secret SECRET

# Extract only, don't create invoice
python ocr_ingest.py --file invoice.pdf --no-create

# Use Google Vision instead of Tesseract
python ocr_ingest.py --file invoice.pdf --ocr-provider google_vision

# Process and save pretty JSON
python ocr_ingest.py --file invoice.pdf -o result.json --pretty
```

## Troubleshooting

### "Tesseract not available"
- Ensure Tesseract is installed
- Set `TESSERACT_CMD` in `.env` if not in PATH

### "Configuration validation failed"
- Check `.env` has all required fields
- Verify ERPNext URL is accessible
- Test API keys in ERPNext

### "No vendor matches found"
- Verify vendor exists in ERPNext
- Lower `VENDOR_MATCH_THRESHOLD` in `.env`
- Check vendor name spelling in invoice

### Low OCR confidence
- Ensure image is clear and high resolution
- Enable preprocessing in `.env`:
  ```env
  ENABLE_PREPROCESSING=true
  DESKEW_ENABLED=true
  DENOISE_ENABLED=true
  ```
- Try Google Vision API for better accuracy

## Next Steps

- Read the full [README.md](README.md)
- Review [EXAMPLE_OUTPUT.json](EXAMPLE_OUTPUT.json)
- Check [CONTRIBUTING.md](CONTRIBUTING.md) to extend functionality
- See [CHANGELOG.md](CHANGELOG.md) for version history

## Sample Workflow

1. **Upload Invoice**: Place invoice PDF/image in a folder
2. **Run OCR**: `python ocr_ingest.py --file invoice.pdf`
3. **Review Output**: Check JSON output for extracted data and confidence
4. **Verify in ERPNext**: Log into ERPNext, find the Draft Purchase Invoice
5. **Review & Submit**: Review the draft, make any corrections, and submit

## Tips

- **Batch Processing**: Use a loop to process multiple invoices
  ```bash
  for file in invoices/*.pdf; do
    python ocr_ingest.py --file "$file" --output "results/$(basename $file).json"
  done
  ```

- **Test First**: Always test with `--no-create` first to verify extraction quality

- **Adjust Thresholds**: Fine-tune matching thresholds based on your vendor names

- **Monitor Confidence**: Track confidence scores to identify problematic invoices

- **Keep Originals**: Original files are attached to Purchase Invoices for reference

## Support

For issues or questions, check:
- [README.md](README.md) - Full documentation
- [GitHub Issues](https://github.com/yourusername/ocr-vendor-bill-ingestion/issues)
- ERPNext Forum for ERPNext-specific questions

Happy processing! 🎉
