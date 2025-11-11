# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-11

### Added
- Initial release of OCR-based Vendor Bill Ingestion for ERPNext
- Support for multiple image formats (PDF, JPG, PNG, TIFF, BMP)
- Tesseract OCR integration with preprocessing
- Optional Google Vision API support
- Automatic field extraction:
  - Vendor name
  - Invoice number
  - Invoice date (with multiple format support)
  - Invoice total and tax amounts
  - Currency detection
  - Line items with quantities and prices
- Fuzzy vendor matching against ERPNext Vendor Master
- Configurable matching thresholds
- Draft Purchase Invoice creation in ERPNext
- Automatic file attachment to created invoices
- Confidence scoring for all extracted fields
- Image preprocessing (deskewing, denoising, thresholding)
- Command-line interface with multiple options
- Comprehensive test suite with mocked ERPNext API
- Detailed documentation and examples
- Demo script for testing without ERPNext
- Sample invoice generator

### Features
- **Multi-page PDF support**: Process multi-page invoices
- **Configurable OCR providers**: Choose between Tesseract and Google Vision
- **Vendor suggestions**: Get top 3 vendor matches when auto-approval threshold not met
- **Audit trail**: JSON output with confidence scores and processing details
- **Error handling**: Comprehensive error reporting with warnings and errors arrays
- **Extensible architecture**: Easy to add new OCR providers and field extractors

### Configuration
- Environment-based configuration with `.env` file
- Configurable thresholds for vendor matching
- Optional image preprocessing toggles
- Adjustable logging levels
- Support for custom Tesseract installation paths

### Documentation
- Comprehensive README with installation and usage instructions
- API documentation via docstrings
- Example output JSON
- Contributing guidelines
- Sample invoices for testing

### Testing
- Unit tests for utility functions
- Mocked tests for ERPNext client
- Field extraction tests with sample data
- Pytest configuration with coverage support

## [Unreleased]

### Planned Features
- Multi-language invoice support
- Web interface for file uploads
- Batch processing capabilities
- Manual review UI in ERPNext
- Confidence heatmap visualization
- Webhook support for callbacks
- Machine learning for invoice-specific training
- Support for additional ERPNext doctypes
- Improved line item detection using table recognition
- Support for more tax types and formats
- Integration with email for automatic invoice ingestion
- REST API endpoint for programmatic access

### Known Issues
- Line item extraction is heuristic-based and may not work for all invoice formats
- Date format detection assumes day-first format by default
- Tax account heads require manual configuration in ERPNext
- Item codes default to generic "Items" - requires customization per deployment

### Compatibility
- Python 3.10+
- ERPNext v15
- Tesseract 4.0+
- Google Vision API v3.4+ (optional)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

This project is provided as-is for use with ERPNext instances.
