# Architecture Documentation

This document describes the architecture and design of the OCR Vendor Bill Ingestion system.

## System Overview

The OCR Vendor Bill Ingestion system is designed as a modular Python application that processes vendor invoices through OCR, extracts structured data, and integrates with ERPNext to create Purchase Invoices.

```
┌─────────────────────────────────────────────────────────────────┐
│                      OCR VENDOR BILL INGESTION                  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                         INPUT LAYER                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  File Formats: PDF, JPG, PNG, TIFF, BMP                  │  │
│  │  Sources: CLI upload, API endpoint (future)              │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PREPROCESSING LAYER                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  • PDF to Image conversion (pdf2image)                   │  │
│  │  • Image enhancement (OpenCV)                            │  │
│  │  • Deskewing                                             │  │
│  │  • Denoising                                             │  │
│  │  • Thresholding & binarization                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                       OCR LAYER                                 │
│  ┌──────────────┐              ┌──────────────────────┐        │
│  │  Tesseract   │              │  Google Vision API   │        │
│  │   (Primary)  │              │     (Optional)       │        │
│  └──────────────┘              └──────────────────────┘        │
│         │                                  │                    │
│         └──────────────┬──────────────────┘                    │
│                        ▼                                        │
│            ┌────────────────────────┐                          │
│            │  OCRResult with text   │                          │
│            │  & confidence scores   │                          │
│            └────────────────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   EXTRACTION LAYER                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Field Extractor (regex + heuristics)                    │  │
│  │  • Vendor name detection                                 │  │
│  │  • Invoice number extraction                             │  │
│  │  • Date parsing (multiple formats)                       │  │
│  │  • Amount extraction (total, tax)                        │  │
│  │  • Currency detection                                    │  │
│  │  • Line item parsing (table detection)                   │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   MATCHING LAYER                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Fuzzy Vendor Matching (rapidfuzz)                       │  │
│  │  • Query ERPNext Vendor Master                           │  │
│  │  • Token-based similarity scoring                        │  │
│  │  • Confidence thresholds                                 │  │
│  │  • Auto-approval or suggestions                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                 INTEGRATION LAYER                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  ERPNext API Client                                      │  │
│  │  • Create Purchase Invoice (Draft)                       │  │
│  │  • Attach original file                                  │  │
│  │  • Set supplier, dates, amounts                          │  │
│  │  • Add line items                                        │  │
│  │  • Apply taxes                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      OUTPUT LAYER                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  JSON Response with:                                     │  │
│  │  • Extracted fields + confidence                         │  │
│  │  • Vendor match details                                  │  │
│  │  • Purchase Invoice ID                                   │  │
│  │  • Warnings & errors                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Configuration Layer (`config.py`)

**Purpose**: Centralized configuration management

**Components**:
- Environment variable loading (`.env`)
- Configuration validation
- Default values
- Regex patterns for extraction
- Threshold settings

**Design Pattern**: Singleton configuration object

### 2. Utility Layer (`utils.py`)

**Purpose**: Reusable utility functions for image processing and text manipulation

**Key Functions**:
- `preprocess_image()`: Image enhancement pipeline
- `convert_pdf_to_images()`: PDF conversion
- `normalize_amount()`: Numeric parsing
- `normalize_date()`: Date parsing
- `detect_currency()`: Currency identification
- `calculate_confidence_score()`: Confidence calculation

**Dependencies**: OpenCV, Pillow, pdf2image, dateutil

### 3. OCR Parser Layer (`ocr_parsers/`)

**Purpose**: Abstract OCR provider interface with multiple implementations

**Structure**:
```
ocr_parsers/
├── base.py              # Abstract base classes
├── tesseract_parser.py  # Tesseract implementation
├── google_vision_parser.py # Google Vision implementation
└── field_extractor.py   # Field extraction logic
```

**Design Pattern**: Strategy pattern for OCR providers

**Key Classes**:
- `OCRParser` (ABC): Abstract interface
- `OCRResult`: Data container for OCR output
- `TesseractParser`: Tesseract implementation
- `GoogleVisionParser`: Google Vision implementation
- `FieldExtractor`: Field extraction from text

### 4. Field Extraction Layer (`ocr_parsers/field_extractor.py`)

**Purpose**: Extract structured invoice data from raw OCR text

**Data Structures**:
- `ExtractedField`: Field value + confidence
- `LineItem`: Invoice line item
- `InvoiceData`: Complete invoice data container

**Extraction Methods**:
- Pattern matching (regex)
- Heuristic analysis
- Keyword detection
- Position-based inference

### 5. ERPNext Integration Layer (`erpnext_client.py`)

**Purpose**: API client for ERPNext operations

**Key Operations**:
- Vendor search and lookup
- Fuzzy vendor matching
- Purchase Invoice creation
- File attachment
- Document retrieval

**Design Pattern**: Repository pattern for ERPNext resources

**Key Classes**:
- `ERPNextClient`: Main API client
- `VendorMatch`: Vendor match result container

**Authentication**: Token-based API authentication

### 6. Application Layer (`ocr_ingest.py`)

**Purpose**: Main application orchestration and CLI

**Components**:
- `InvoiceIngestion`: Main orchestration class
- CLI interface (Click)
- End-to-end processing pipeline
- Error handling and logging

**Processing Flow**:
1. Load and validate input file
2. Perform OCR with selected provider
3. Extract structured fields
4. Match vendor in ERPNext
5. Create Purchase Invoice (optional)
6. Attach file (optional)
7. Return JSON result

## Data Flow

### Complete Processing Pipeline

```
Invoice File
    │
    ├─→ Load Image(s) ─────────────────────────┐
    │                                           │
    │   PDF?                                    │
    │   ├─ Yes → pdf2image                     │
    │   └─ No → PIL.Image.open                 │
    │                                           │
    ├─→ Preprocess ─────────────────────────── │
    │   ├─ Grayscale conversion                │
    │   ├─ Denoising                            │
    │   ├─ Deskewing                            │
    │   └─ Thresholding                         │
    │                                           │
    ├─→ OCR ────────────────────────────────── │
    │   ├─ Tesseract: pytesseract              │
    │   └─ Google Vision: API call             │
    │                                           │
    ├─→ Extract Fields ────────────────────────│
    │   ├─ Vendor name (top lines, keywords)   │
    │   ├─ Invoice number (regex patterns)     │
    │   ├─ Date (multiple format support)      │
    │   ├─ Amounts (total, tax)                │
    │   └─ Line items (table parsing)          │
    │                                           │
    ├─→ Fuzzy Match Vendor ────────────────────│
    │   ├─ Query ERPNext vendors               │
    │   ├─ Calculate similarity scores         │
    │   ├─ Apply threshold                     │
    │   └─ Auto-approve or suggest             │
    │                                           │
    ├─→ Create Purchase Invoice ───────────────│
    │   ├─ Build document structure            │
    │   ├─ POST to ERPNext API                 │
    │   └─ Attach original file                │
    │                                           │
    └─→ Return JSON Result ────────────────────┘
        ├─ Extracted fields + confidence
        ├─ Vendor match details
        ├─ Purchase Invoice ID
        └─ Warnings & errors
```

## Design Principles

### 1. Modularity
- Each layer has clear responsibilities
- Components are loosely coupled
- Easy to extend with new providers

### 2. Configurability
- Environment-based configuration
- No hardcoded values
- Runtime provider selection

### 3. Testability
- Dependency injection
- Mocked external services
- Unit tests for all components

### 4. Extensibility
- Abstract interfaces for OCR providers
- Plugin architecture for field extractors
- Easy to add new features

### 5. Robustness
- Comprehensive error handling
- Graceful degradation
- Detailed logging

### 6. Security
- No credentials in code
- Environment variable configuration
- HTTPS for API communication

## Key Design Decisions

### 1. OCR Provider Abstraction

**Decision**: Use abstract base class for OCR providers

**Rationale**:
- Allows easy addition of new OCR engines
- Consistent interface across providers
- Runtime provider selection

### 2. Confidence Scoring

**Decision**: Include confidence scores for all extracted fields

**Rationale**:
- Enables quality assessment
- Supports manual review workflows
- Identifies problematic extractions

### 3. Fuzzy Vendor Matching

**Decision**: Use fuzzy matching instead of exact match

**Rationale**:
- Handles OCR errors
- Accommodates name variations
- Improves match success rate

### 4. Draft Invoice Creation

**Decision**: Create invoices in Draft state

**Rationale**:
- Allows manual review before posting
- Prevents erroneous postings
- Supports audit workflow

### 5. File Attachment

**Decision**: Attach original file to Purchase Invoice

**Rationale**:
- Maintains audit trail
- Enables verification
- Supports compliance requirements

## Extension Points

### Adding a New OCR Provider

1. Create new parser class inheriting from `OCRParser`
2. Implement `extract_text()` method
3. Implement `is_available()` method
4. Register in `ocr_parsers/__init__.py`
5. Add configuration options
6. Update CLI to support new provider

### Adding New Field Types

1. Add field to `InvoiceData` dataclass
2. Implement extraction method in `FieldExtractor`
3. Add to `to_dict()` method
4. Update tests
5. Update documentation

### Supporting New ERPNext Doctypes

1. Add new method to `ERPNextClient`
2. Define data structure
3. Implement API call
4. Add tests
5. Update CLI if needed

## Performance Considerations

### Image Processing
- Convert PDF pages one at a time (streaming)
- Limit image resolution to reasonable DPI (300)
- Cache preprocessed images if processing multiple times

### OCR
- Tesseract is faster but less accurate
- Google Vision is slower but more accurate
- Consider async processing for batch operations

### API Calls
- Batch vendor lookups when possible
- Cache vendor list for repeated matching
- Respect ERPNext rate limits

## Security Considerations

### Credentials
- Store in environment variables
- Never commit to version control
- Use secure credential management in production

### File Handling
- Validate file types
- Limit file sizes
- Scan for malware if accepting uploads

### API Security
- Use HTTPS only
- Token-based authentication
- Validate all inputs

## Monitoring and Logging

### Logging Levels
- **DEBUG**: Detailed processing steps
- **INFO**: High-level operations
- **WARNING**: Non-critical issues
- **ERROR**: Processing failures

### Key Metrics
- OCR confidence scores
- Vendor match confidence
- Processing time
- Success/failure rates

## Future Enhancements

### 1. Machine Learning
- Train custom models for invoice formats
- Improve line item detection
- Learn from corrections

### 2. Web Interface
- File upload UI
- Real-time processing status
- Visual review tools

### 3. Batch Processing
- Process multiple invoices in parallel
- Queue-based architecture
- Progress tracking

### 4. Enhanced Matching
- Learn from successful matches
- Multi-field vendor matching
- Vendor alias support

### 5. Integration Expansion
- Email ingestion
- Cloud storage integration
- Webhook notifications

## Dependencies

### Core Dependencies
- **pytesseract**: Tesseract OCR wrapper
- **Pillow**: Image processing
- **pdf2image**: PDF conversion
- **opencv-python**: Advanced image processing
- **requests**: HTTP client
- **rapidfuzz**: Fuzzy string matching
- **python-dateutil**: Date parsing
- **python-dotenv**: Environment configuration
- **click**: CLI framework

### Optional Dependencies
- **google-cloud-vision**: Google Vision API

### Development Dependencies
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking support

## Conclusion

This architecture provides a solid foundation for OCR-based invoice ingestion with clear separation of concerns, extensibility, and production-ready features. The modular design allows for easy maintenance and enhancement while maintaining code quality and testability.
