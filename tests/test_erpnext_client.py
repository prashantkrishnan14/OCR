"""
Tests for ERPNext client with mocked API calls.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from erpnext_client import ERPNextClient, VendorMatch


@pytest.fixture
def mock_session():
    """Mock requests session."""
    with patch("erpnext_client.requests.Session") as mock:
        session = MagicMock()
        mock.return_value = session
        yield session


@pytest.fixture
def client(mock_session):
    """Create ERPNext client with mocked session."""
    client = ERPNextClient(
        url="https://erp.test.com",
        api_key="test_key",
        api_secret="test_secret",
    )
    client.session = mock_session
    return client


class TestERPNextClient:
    """Tests for ERPNext client."""

    def test_initialization(self):
        """Test client initialization."""
        client = ERPNextClient(
            url="https://erp.test.com",
            api_key="key",
            api_secret="secret",
        )
        assert client.url == "https://erp.test.com"
        assert client.api_key == "key"
        assert client.api_secret == "secret"

    def test_test_connection_success(self, client, mock_session):
        """Test successful connection test."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.get.return_value = mock_response

        assert client.test_connection() is True

    def test_test_connection_failure(self, client, mock_session):
        """Test failed connection test."""
        mock_session.get.side_effect = Exception("Connection failed")

        assert client.test_connection() is False

    def test_search_vendors(self, client, mock_session):
        """Test vendor search."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"name": "VND-001", "supplier_name": "Acme Supplies Pvt Ltd"},
                {"name": "VND-002", "supplier_name": "Beta Corp"},
            ]
        }
        mock_session.get.return_value = mock_response

        vendors = client.search_vendors("Acme")

        assert len(vendors) == 2
        assert vendors[0]["supplier_name"] == "Acme Supplies Pvt Ltd"

    def test_fuzzy_match_vendor_high_confidence(self, client, mock_session):
        """Test fuzzy matching with high confidence."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"name": "VND-001", "supplier_name": "ACME SUPPLIES PVT LTD"},
                {"name": "VND-002", "supplier_name": "Beta Corp"},
            ]
        }
        mock_session.get.return_value = mock_response

        best_match, suggestions = client.fuzzy_match_vendor("Acme Supplies Pvt Ltd")

        assert best_match is not None
        assert best_match.erp_id == "VND-001"
        assert len(suggestions) > 0

    def test_fuzzy_match_vendor_low_confidence(self, client, mock_session):
        """Test fuzzy matching with low confidence."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {"name": "VND-001", "supplier_name": "Completely Different Name"},
            ]
        }
        mock_session.get.return_value = mock_response

        best_match, suggestions = client.fuzzy_match_vendor("Acme Supplies")

        # Should return None for best_match if below auto-approve threshold
        # but may have suggestions
        assert isinstance(suggestions, list)

    def test_create_purchase_invoice(self, client, mock_session):
        """Test Purchase Invoice creation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "name": "PINV-00012",
                "docstatus": 0,
            }
        }
        mock_session.post.return_value = mock_response

        result = client.create_purchase_invoice(
            supplier="VND-001",
            invoice_number="INV-2025-0099",
            posting_date="2025-11-08",
            grand_total=41200.00,
            currency="INR",
        )

        assert result["name"] == "PINV-00012"
        assert mock_session.post.called

    def test_create_purchase_invoice_with_line_items(self, client, mock_session):
        """Test Purchase Invoice creation with line items."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "name": "PINV-00013",
                "docstatus": 0,
            }
        }
        mock_session.post.return_value = mock_response

        line_items = [
            {"description": "Item 1", "qty": 10, "unit_price": 100, "line_total": 1000},
            {"description": "Item 2", "qty": 5, "unit_price": 200, "line_total": 1000},
        ]

        result = client.create_purchase_invoice(
            supplier="VND-001",
            invoice_number="INV-2025-0100",
            posting_date="2025-11-08",
            grand_total=2000.00,
            currency="INR",
            line_items=line_items,
        )

        assert result["name"] == "PINV-00013"


class TestVendorMatch:
    """Tests for VendorMatch class."""

    def test_vendor_match_creation(self):
        """Test VendorMatch object creation."""
        match = VendorMatch("VND-001", "Acme Corp", 89.5)

        assert match.erp_id == "VND-001"
        assert match.name == "Acme Corp"
        assert match.confidence == 89.5

    def test_vendor_match_to_dict(self):
        """Test VendorMatch to_dict conversion."""
        match = VendorMatch("VND-001", "Acme Corp", 89.5)
        result = match.to_dict()

        assert result["erp_id"] == "VND-001"
        assert result["name"] == "Acme Corp"
        assert result["confidence"] == 0.895  # Converted to 0-1 scale
