# OCR-Based Vendor Bill Ingestion for ERPNext

A Python application that implements OCR-based vendor bill ingestion for ERPNext, similar to Xero's bill capture feature. Upload a vendor bill (PDF/image), and the system extracts vendor information, invoice details, and line items, then creates a Draft Purchase Invoice in ERPNext.

## Features

- **Multi-format Support**: Accepts PDF, JPG, PNG, TIFF, and BMP files
- **Intelligent OCR**: Uses Tesseract (with optional Google Vision API support)
- **Field Extraction**: Automatically extracts:
  - Vendor name
  - Invoice number
  - Invoice date
  - Invoice total and tax amounts
  - Currency
  - Line items (description, quantity, price)
- **Fuzzy Vendor Matching**: Matches extracted vendor names against ERPNext Vendor Master
- **ERPNext Integration**: Creates Draft Purchase Invoices with extracted data
- **File Attachment**: Attaches original invoice file to the Purchase Invoice
- **Audit Trail**: Provides confidence scores for all extracted fields
- **Image Preprocessing**: Automatic deskewing, denoising, and thresholding

## Requirements

- Python 3.10+
- Tesseract OCR engine
- ERPNext v15 (or compatible version)
- Dependencies listed in `requirements.txt`

## Installation

### 1. Install System Dependencies

#### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr libtesseract-dev poppler-utils
```

#### macOS:
```bash
brew install tesseract poppler
```

#### Windows:
Download and install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Copy the example environment file and configure it:

```bash
cp .env.example .env
```

Edit `.env` and set your ERPNext credentials:

```env
ERPNEXT_URL=https://your-erpnext-instance.com
ERPNEXT_API_KEY=your_api_key
ERPNEXT_API_SECRET=your_api_secret

# Optional: Set Tesseract path if not in system PATH
TESSERACT_CMD=/usr/bin/tesseract

# Optional: For Google Vision API
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
OCR_PROVIDER=tesseract
```

### 4. Generate ERPNext API Keys

1. Log in to your ERPNext instance
2. Go to User → API Access
3. Generate API Key and Secret
4. Add these to your `.env` file

## Usage

### Basic Usage

Process an invoice and create a Purchase Invoice:

```bash
python ocr_ingest.py --file sample_invoices/invoice.pdf
```

### Extract Data Only (Don't Create Invoice)

```bash
python ocr_ingest.py --file invoice.pdf --no-create
```

### With Custom ERPNext Credentials

```bash
python ocr_ingest.py \
  --file invoice.pdf \
  --erp-url https://erp.example.com \
  --api-key YOUR_KEY \
  --api-secret YOUR_SECRET
```

### Save Output to JSON File

```bash
python ocr_ingest.py --file invoice.pdf --output result.json --pretty
```

### Use Google Vision API

```bash
python ocr_ingest.py --file invoice.pdf --ocr-provider google_vision
```

## CLI Options

- `--file, -f`: Path to invoice file (required)
- `--erp-url`: ERPNext instance URL
- `--api-key`: ERPNext API key
- `--api-secret`: ERPNext API secret
- `--ocr-provider`: OCR provider (`tesseract` or `google_vision`)
- `--no-create`: Extract data only, don't create Purchase Invoice
- `--no-attach`: Don't attach file to Purchase Invoice
- `--output, -o`: Output JSON file path
- `--pretty`: Pretty print JSON output

## Output Format

The application returns a JSON object with the following structure:

```json
{
  "file": "/path/to/invoice.pdf",
  "vendor_name": {
    "value": "Acme Supplies Pvt Ltd",
    "confidence": 0.92
  },
  "invoice_number": {
    "value": "INV-2025-0099",
    "confidence": 0.96
  },
  "invoice_date": {
    "value": "2025-11-08",
    "confidence": 0.9
  },
  "invoice_total": {
    "value": 41200.0,
    "currency": "INR",
    "confidence": 0.95
  },
  "tax_amount": {
    "value": 7200.0,
    "currency": "INR",
    "confidence": 0.88
  },
  "line_items": [
    {
      "description": "Cable ties 100mm",
      "qty": 10,
      "unit_price": 150.0,
      "line_total": 1500.0,
      "confidence": 0.75
    }
  ],
  "vendor_match": {
    "erp_id": "VND-0001",
    "name": "ACME SUPPLIES PVT LTD",
    "confidence": 0.89
  },
  "purchase_invoice_created": {
    "docname": "PINV-00012",
    "status": "Draft"
  },
  "warnings": [],
  "errors": []
}
```

## Configuration

### Fuzzy Matching Thresholds

Adjust vendor matching sensitivity in `.env`:

```env
VENDOR_MATCH_THRESHOLD=75        # Minimum score to consider a match
VENDOR_AUTO_APPROVE_THRESHOLD=85 # Auto-approve above this score
```

### Image Preprocessing

Enable/disable preprocessing options:

```env
ENABLE_PREPROCESSING=true
DESKEW_ENABLED=true
DENOISE_ENABLED=true
```

### Logging

Set logging level:

```env
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR
```

## Project Structure

```
OCR/
├── ocr_ingest.py              # Main CLI application
├── config.py                  # Configuration management
├── utils.py                   # Image preprocessing and helpers
├── erpnext_client.py         # ERPNext API wrapper
├── ocr_parsers/              # OCR parsing modules
│   ├── __init__.py
│   ├── base.py               # Base OCR parser interface
│   ├── tesseract_parser.py  # Tesseract implementation
│   ├── google_vision_parser.py # Google Vision implementation
│   └── field_extractor.py   # Field extraction logic
├── tests/                    # Unit tests
│   ├── test_utils.py
│   ├── test_erpnext_client.py
│   └── test_field_extractor.py
├── sample_invoices/          # Sample invoice files
├── requirements.txt          # Python dependencies
├── .env.example             # Example environment configuration
└── README.md                # This file
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_utils.py
```

### Adding a New OCR Provider

1. Create a new parser class in `ocr_parsers/` inheriting from `OCRParser`
2. Implement `extract_text()` and `is_available()` methods
3. Register the provider in `ocr_ingest.py`
4. Add configuration options to `config.py`

## How It Works

1. **File Loading**: Loads PDF or image file, converting PDF pages to images
2. **Image Preprocessing**: Applies deskewing, denoising, and thresholding
3. **OCR Extraction**: Extracts text using Tesseract or Google Vision API
4. **Field Parsing**: Uses regex patterns and heuristics to extract structured data
5. **Vendor Matching**: Performs fuzzy matching against ERPNext Vendor Master
6. **Invoice Creation**: Creates Draft Purchase Invoice in ERPNext
7. **File Attachment**: Attaches original file to the created invoice

## Limitations and Considerations

- **Line Item Extraction**: Line item extraction is heuristic-based and works best with well-formatted invoices
- **OCR Accuracy**: Accuracy depends on image quality and invoice format
- **Language Support**: Currently optimized for English invoices
- **Vendor Matching**: Requires vendors to be pre-configured in ERPNext
- **ERPNext Item Codes**: Line items use a default "Items" code; customize in `erpnext_client.py`
- **Tax Accounts**: Tax account heads should be configured in ERPNext

## Troubleshooting

### Tesseract Not Found

```
Error: Tesseract not available
```

**Solution**: Install Tesseract and ensure it's in your PATH, or set `TESSERACT_CMD` in `.env`

### Low OCR Confidence

```
Warning: Low OCR confidence: 0.42
```

**Solution**:
- Ensure image is clear and high resolution (300 DPI recommended)
- Enable preprocessing: `ENABLE_PREPROCESSING=true`
- Try Google Vision API for better accuracy

### No Vendor Match

```
Error: No vendor found matching: <vendor_name>
```

**Solution**:
- Ensure the vendor exists in ERPNext
- Check vendor name spelling
- Lower `VENDOR_MATCH_THRESHOLD` in `.env`

### API Authentication Failed

```
Error: Connection test failed
```

**Solution**:
- Verify `ERPNEXT_URL`, `ERPNEXT_API_KEY`, and `ERPNEXT_API_SECRET` are correct
- Ensure API key has appropriate permissions
- Check network connectivity to ERPNext instance

## Optional Enhancements

The following enhancements can be implemented:

- **Multi-language Support**: Add language detection and support for non-English invoices
- **Web Interface**: Create a Flask/FastAPI web interface for file uploads
- **Batch Processing**: Process multiple invoices in parallel
- **Manual Review UI**: ERPNext doctype for reviewing unconfirmed OCR imports
- **Confidence Heatmap**: Visual overlay showing confidence scores on invoice image
- **Webhook Support**: Trigger callbacks after invoice creation
- **Machine Learning**: Train custom models for specific invoice formats

## Security

- API keys and secrets are stored in environment variables, not in code
- Files are handled securely without storing intermediate data
- All ERPNext communication uses HTTPS
- API authentication uses token-based auth

## License

This project is provided as-is for use with ERPNext instances.

## Support

For issues, questions, or contributions, please refer to the project repository.

## Example Sample Invoice

A sample invoice text format that works well:

```
ACME SUPPLIES PVT LTD
123 Business Street, City

INVOICE

Invoice Number: INV-2025-0099
Date: 08/11/2025

Description                 Qty    Rate      Amount
Cable ties 100mm            10     150.00    1,500.00
Zip ties 200mm              20   1,250.00   25,000.00

Subtotal:                                   26,500.00
GST @ 18%:                                   4,770.00
TOTAL:                                      ₹ 31,270.00
```

## Acknowledgments

- Tesseract OCR by Google
- ERPNext by Frappe Technologies
- Python libraries: Pillow, OpenCV, pdf2image, rapidfuzz
