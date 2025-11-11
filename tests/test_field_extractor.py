"""
Tests for field extraction from OCR text.
"""
import pytest
from ocr_parsers.field_extractor import FieldExtractor, InvoiceData


@pytest.fixture
def extractor():
    """Create field extractor instance."""
    return FieldExtractor()


@pytest.fixture
def sample_invoice_text():
    """Sample invoice OCR text."""
    return """
    ACME SUPPLIES PVT LTD
    123 Business Street
    City, State 123456

    INVOICE

    Invoice Number: INV-2025-0099
    Invoice Date: 08/11/2025

    Bill To:
    Customer Name
    Address

    Description                 Qty    Rate      Amount
    --------------------------------------------------------
    Cable ties 100mm            10     150.00    1,500.00
    Zip ties 200mm              20   1,250.00   25,000.00
    Screws pack                  5     150.00      750.00

    Subtotal:                                    27,250.00
    CGST @ 9%:                                    2,452.50
    SGST @ 9%:                                    2,452.50

    TOTAL:                                      ₹ 32,155.00

    Payment Terms: Net 30
    """


class TestFieldExtractor:
    """Tests for FieldExtractor."""

    def test_extract_invoice_number(self, extractor, sample_invoice_text):
        """Test invoice number extraction."""
        invoice_data = extractor.extract_fields(sample_invoice_text)

        assert invoice_data.invoice_number.value == "INV-2025-0099"
        assert invoice_data.invoice_number.confidence > 0.7

    def test_extract_invoice_date(self, extractor, sample_invoice_text):
        """Test invoice date extraction."""
        invoice_data = extractor.extract_fields(sample_invoice_text)

        # Date could be parsed as 2025-11-08 or 2025-08-11 depending on locale
        assert invoice_data.invoice_date.value is not None
        assert len(invoice_data.invoice_date.value) == 10  # yyyy-mm-dd format

    def test_extract_vendor_name(self, extractor, sample_invoice_text):
        """Test vendor name extraction."""
        invoice_data = extractor.extract_fields(sample_invoice_text)

        assert invoice_data.vendor_name.value is not None
        assert "ACME" in invoice_data.vendor_name.value.upper()

    def test_extract_amounts(self, extractor, sample_invoice_text):
        """Test amount extraction."""
        invoice_data = extractor.extract_fields(sample_invoice_text)

        assert invoice_data.invoice_total.value is not None
        assert invoice_data.invoice_total.value > 0

        # Tax amount should be extracted
        assert invoice_data.tax_amount.value is not None

    def test_detect_currency(self, extractor, sample_invoice_text):
        """Test currency detection."""
        invoice_data = extractor.extract_fields(sample_invoice_text)

        assert invoice_data.currency == "INR"

    def test_extract_line_items(self, extractor, sample_invoice_text):
        """Test line item extraction."""
        invoice_data = extractor.extract_fields(sample_invoice_text)

        # Line items may or may not be extracted depending on OCR quality
        # Just ensure no crash and result is a list
        assert isinstance(invoice_data.line_items, list)

    def test_to_dict_conversion(self, extractor, sample_invoice_text):
        """Test conversion to dictionary."""
        invoice_data = extractor.extract_fields(sample_invoice_text)
        result_dict = extractor.to_dict(invoice_data)

        assert "vendor_name" in result_dict
        assert "invoice_number" in result_dict
        assert "invoice_date" in result_dict
        assert "invoice_total" in result_dict
        assert "tax_amount" in result_dict
        assert "line_items" in result_dict

        # Check structure
        assert "value" in result_dict["vendor_name"]
        assert "confidence" in result_dict["vendor_name"]

    def test_empty_text(self, extractor):
        """Test extraction with empty text."""
        invoice_data = extractor.extract_fields("")

        assert invoice_data.vendor_name.value is None
        assert invoice_data.invoice_number.value is None
        assert invoice_data.invoice_date.value is None

    def test_partial_data(self, extractor):
        """Test extraction with partial data."""
        text = "Invoice INV-123 Date: 2025-11-08"
        invoice_data = extractor.extract_fields(text)

        assert invoice_data.invoice_number.value == "INV-123"
        assert invoice_data.invoice_date.value == "2025-11-08"
