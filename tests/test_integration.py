"""
Integration tests for the complete OCR ingestion workflow.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from PIL import Image
import io

from ocr_ingest import InvoiceIngestion


@pytest.fixture
def mock_image():
    """Create a mock invoice image."""
    # Create a simple white image with text
    img = Image.new('RGB', (800, 1000), 'white')
    return img


@pytest.fixture
def mock_invoice_text():
    """Mock OCR extracted text."""
    return """
    ACME SUPPLIES PVT LTD
    123 Business Street

    INVOICE

    Invoice Number: INV-2025-0099
    Date: 08/11/2025

    Description                 Qty    Rate      Amount
    Cable ties 100mm            10     150.00    1,500.00
    Zip ties 200mm              20   1,250.00   25,000.00

    Subtotal:                                   26,500.00
    GST @ 18%:                                   4,770.00
    TOTAL:                                      ₹ 31,270.00
    """


@pytest.fixture
def mock_erp_vendors():
    """Mock ERPNext vendor data."""
    return {
        "data": [
            {"name": "VND-001", "supplier_name": "ACME SUPPLIES PVT LTD"},
            {"name": "VND-002", "supplier_name": "Beta Corp Ltd"},
        ]
    }


@pytest.fixture
def mock_purchase_invoice():
    """Mock created Purchase Invoice."""
    return {
        "name": "PINV-00012",
        "docstatus": 0,
        "supplier": "VND-001",
        "bill_no": "INV-2025-0099",
    }


class TestInvoiceIngestionIntegration:
    """Integration tests for complete invoice processing."""

    @patch('ocr_ingest.ERPNextClient')
    @patch('ocr_ingest.TesseractParser')
    @patch('utils.load_image')
    def test_complete_workflow(
        self,
        mock_load_image,
        mock_parser_class,
        mock_client_class,
        mock_image,
        mock_invoice_text,
        mock_erp_vendors,
        mock_purchase_invoice,
    ):
        """Test complete end-to-end workflow."""
        # Setup mocks
        mock_load_image.return_value = [mock_image]

        # Mock OCR parser
        mock_parser = MagicMock()
        mock_parser.is_available.return_value = True
        mock_parser.extract_text.return_value = MagicMock(
            text=mock_invoice_text,
            confidence=0.92,
            metadata={}
        )
        mock_parser.extract_text_from_multiple.return_value = [
            MagicMock(text=mock_invoice_text, confidence=0.92, metadata={})
        ]
        mock_parser_class.return_value = mock_parser

        # Mock ERPNext client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Mock vendor search
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_erp_vendors
        mock_client.session.get.return_value = mock_response
        mock_client.search_vendors.return_value = mock_erp_vendors["data"]

        # Mock fuzzy matching
        from erpnext_client import VendorMatch
        mock_vendor_match = VendorMatch("VND-001", "ACME SUPPLIES PVT LTD", 95.0)
        mock_client.fuzzy_match_vendor.return_value = (
            mock_vendor_match,
            [mock_vendor_match]
        )

        # Mock Purchase Invoice creation
        mock_client.create_purchase_invoice.return_value = mock_purchase_invoice

        # Create ingestion instance
        ingestion = InvoiceIngestion(
            erp_url="https://test.erp.com",
            api_key="test_key",
            api_secret="test_secret",
        )

        # Process invoice
        result = ingestion.process_invoice(
            file_path=Path("test_invoice.pdf"),
            create_invoice=True,
            attach_file=False,
        )

        # Assertions
        assert "vendor_name" in result
        assert result["vendor_name"]["value"] == "ACME SUPPLIES PVT LTD"

        assert "invoice_number" in result
        assert result["invoice_number"]["value"] == "INV-2025-0099"

        assert "invoice_date" in result
        assert result["invoice_date"]["value"] is not None

        assert "invoice_total" in result
        assert result["invoice_total"]["value"] > 0

        assert "vendor_match" in result
        assert result["vendor_match"]["erp_id"] == "VND-001"

        assert "purchase_invoice_created" in result
        assert result["purchase_invoice_created"]["docname"] == "PINV-00012"

        assert len(result["errors"]) == 0

    @patch('ocr_ingest.ERPNextClient')
    @patch('ocr_ingest.TesseractParser')
    @patch('utils.load_image')
    def test_extraction_only_workflow(
        self,
        mock_load_image,
        mock_parser_class,
        mock_client_class,
        mock_image,
        mock_invoice_text,
    ):
        """Test extraction without creating Purchase Invoice."""
        # Setup mocks
        mock_load_image.return_value = [mock_image]

        mock_parser = MagicMock()
        mock_parser.is_available.return_value = True
        mock_parser.extract_text_from_multiple.return_value = [
            MagicMock(text=mock_invoice_text, confidence=0.92, metadata={})
        ]
        mock_parser_class.return_value = mock_parser

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Create ingestion instance
        ingestion = InvoiceIngestion(
            erp_url="https://test.erp.com",
            api_key="test_key",
            api_secret="test_secret",
        )

        # Process invoice without creating
        result = ingestion.process_invoice(
            file_path=Path("test_invoice.pdf"),
            create_invoice=False,
            attach_file=False,
        )

        # Assertions
        assert "vendor_name" in result
        assert "invoice_number" in result
        assert "invoice_date" in result
        assert "invoice_total" in result

        # Should not create Purchase Invoice
        assert "purchase_invoice_created" not in result or result["purchase_invoice_created"] is None

    @patch('ocr_ingest.ERPNextClient')
    @patch('ocr_ingest.TesseractParser')
    @patch('utils.load_image')
    def test_no_vendor_match_workflow(
        self,
        mock_load_image,
        mock_parser_class,
        mock_client_class,
        mock_image,
        mock_invoice_text,
    ):
        """Test workflow when vendor is not found."""
        # Setup mocks
        mock_load_image.return_value = [mock_image]

        mock_parser = MagicMock()
        mock_parser.is_available.return_value = True
        mock_parser.extract_text_from_multiple.return_value = [
            MagicMock(text=mock_invoice_text, confidence=0.92, metadata={})
        ]
        mock_parser_class.return_value = mock_parser

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_client.search_vendors.return_value = []
        mock_client.fuzzy_match_vendor.return_value = (None, [])

        # Create ingestion instance
        ingestion = InvoiceIngestion(
            erp_url="https://test.erp.com",
            api_key="test_key",
            api_secret="test_secret",
        )

        # Process invoice
        result = ingestion.process_invoice(
            file_path=Path("test_invoice.pdf"),
            create_invoice=True,
            attach_file=False,
        )

        # Assertions
        assert "vendor_name" in result
        assert "errors" in result
        assert len(result["errors"]) > 0
        assert any("vendor" in error.lower() for error in result["errors"])

        # Should not create Purchase Invoice
        assert "purchase_invoice_created" not in result or result["purchase_invoice_created"] is None

    @patch('ocr_ingest.ERPNextClient')
    @patch('ocr_ingest.TesseractParser')
    @patch('utils.load_image')
    def test_low_confidence_warning(
        self,
        mock_load_image,
        mock_parser_class,
        mock_client_class,
        mock_image,
    ):
        """Test that low OCR confidence generates warning."""
        # Setup mocks
        mock_load_image.return_value = [mock_image]

        mock_parser = MagicMock()
        mock_parser.is_available.return_value = True
        mock_parser.extract_text_from_multiple.return_value = [
            MagicMock(text="barely readable text", confidence=0.3, metadata={})
        ]
        mock_parser_class.return_value = mock_parser

        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Create ingestion instance
        ingestion = InvoiceIngestion(
            erp_url="https://test.erp.com",
            api_key="test_key",
            api_secret="test_secret",
        )

        # Process invoice
        result = ingestion.process_invoice(
            file_path=Path("test_invoice.pdf"),
            create_invoice=False,
        )

        # Assertions
        assert "warnings" in result
        assert len(result["warnings"]) > 0
        assert any("confidence" in warning.lower() for warning in result["warnings"])
