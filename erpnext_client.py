"""
ERPNext API client for vendor lookup and Purchase Invoice creation.
"""
import logging
import base64
from typing import Optional
from pathlib import Path

import requests
from rapidfuzz import fuzz, process

from config import config

logger = logging.getLogger(__name__)


class VendorMatch:
    """Container for vendor match result."""

    def __init__(self, erp_id: str, name: str, confidence: float):
        self.erp_id = erp_id
        self.name = name
        self.confidence = confidence

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "erp_id": self.erp_id,
            "name": self.name,
            "confidence": round(self.confidence / 100.0, 2),  # Convert to 0-1 scale
        }


class ERPNextClient:
    """Client for interacting with ERPNext API."""

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
    ):
        """
        Initialize ERPNext client.

        Args:
            url: ERPNext instance URL
            api_key: API key for authentication
            api_secret: API secret for authentication
        """
        self.url = (url or config.ERPNEXT_URL).rstrip("/")
        self.api_key = api_key or config.ERPNEXT_API_KEY
        self.api_secret = api_secret or config.ERPNEXT_API_SECRET

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"token {self.api_key}:{self.api_secret}",
                "Content-Type": "application/json",
            }
        )

    def test_connection(self) -> bool:
        """
        Test connection to ERPNext instance.

        Returns:
            True if connection successful
        """
        try:
            response = self.session.get(f"{self.url}/api/method/frappe.auth.get_logged_user")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def search_vendors(self, query: str, limit: int = 50) -> list[dict]:
        """
        Search for vendors in ERPNext.

        Args:
            query: Search query (vendor name)
            limit: Maximum number of results

        Returns:
            List of vendor dictionaries
        """
        try:
            url = f"{self.url}/api/resource/Supplier"

            params = {
                "fields": '["name", "supplier_name", "supplier_type"]',
                "limit_page_length": limit,
            }

            # If query provided, filter by name
            if query:
                params["filters"] = f'[["supplier_name", "like", "%{query}%"]]'

            response = self.session.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            vendors = data.get("data", [])

            logger.info(f"Found {len(vendors)} vendors matching '{query}'")
            return vendors

        except Exception as e:
            logger.error(f"Error searching vendors: {e}")
            return []

    def fuzzy_match_vendor(
        self, vendor_name: str, threshold: Optional[int] = None
    ) -> tuple[Optional[VendorMatch], list[VendorMatch]]:
        """
        Perform fuzzy matching to find vendor in ERPNext.

        Args:
            vendor_name: Vendor name from OCR
            threshold: Minimum match score (0-100), uses config default if not provided

        Returns:
            Tuple of (best_match or None, top_3_suggestions)
        """
        if not vendor_name:
            return None, []

        threshold = threshold or config.VENDOR_MATCH_THRESHOLD
        auto_approve_threshold = config.VENDOR_AUTO_APPROVE_THRESHOLD

        # Get all vendors
        vendors = self.search_vendors("")

        if not vendors:
            logger.warning("No vendors found in ERPNext")
            return None, []

        # Build list of vendor names for fuzzy matching
        vendor_names = {v["name"]: v["supplier_name"] for v in vendors}

        # Perform fuzzy matching
        matches = process.extract(
            vendor_name,
            vendor_names.values(),
            scorer=fuzz.token_sort_ratio,
            limit=5,
        )

        # Convert to VendorMatch objects
        vendor_matches = []
        for matched_name, score, _ in matches:
            if score >= threshold:
                # Find the vendor ID for this name
                vendor_id = next(
                    (k for k, v in vendor_names.items() if v == matched_name), None
                )
                if vendor_id:
                    vendor_matches.append(VendorMatch(vendor_id, matched_name, score))

        if not vendor_matches:
            logger.warning(f"No vendor matches found for '{vendor_name}' above threshold {threshold}")
            return None, []

        # Best match
        best_match = vendor_matches[0]

        # Top 3 suggestions
        suggestions = vendor_matches[:3]

        # Auto-approve if above threshold
        if best_match.confidence >= auto_approve_threshold:
            logger.info(
                f"Auto-approved vendor match: {best_match.name} "
                f"(confidence: {best_match.confidence})"
            )
            return best_match, suggestions
        else:
            logger.info(
                f"Vendor match below auto-approve threshold: {best_match.name} "
                f"(confidence: {best_match.confidence})"
            )
            return None, suggestions

    def create_purchase_invoice(
        self,
        supplier: str,
        invoice_number: str,
        posting_date: str,
        grand_total: float,
        currency: str = "INR",
        tax_amount: Optional[float] = None,
        line_items: Optional[list[dict]] = None,
    ) -> dict:
        """
        Create a Purchase Invoice in ERPNext as Draft.

        Args:
            supplier: Supplier ID (name field)
            invoice_number: Bill number
            posting_date: Invoice date (yyyy-mm-dd)
            grand_total: Total amount
            currency: Currency code
            tax_amount: Tax amount if available
            line_items: List of line item dictionaries

        Returns:
            Created Purchase Invoice document
        """
        try:
            # Build line items
            items = []

            if line_items and len(line_items) > 0:
                for item in line_items:
                    items.append(
                        {
                            "item_code": "Items",  # Default item code, should be configured
                            "item_name": item.get("description", "Item"),
                            "description": item.get("description", ""),
                            "qty": item.get("qty", 1),
                            "rate": item.get("unit_price", 0),
                            "amount": item.get("line_total", 0),
                        }
                    )
            else:
                # Create single line item with total amount
                items.append(
                    {
                        "item_code": "Items",  # Default item code
                        "item_name": "Invoice Item",
                        "description": f"Invoice {invoice_number}",
                        "qty": 1,
                        "rate": grand_total,
                        "amount": grand_total,
                    }
                )

            # Build invoice document
            invoice_doc = {
                "doctype": "Purchase Invoice",
                "supplier": supplier,
                "bill_no": invoice_number,
                "posting_date": posting_date,
                "currency": currency,
                "items": items,
                "docstatus": 0,  # 0 = Draft
            }

            # Add taxes if provided
            if tax_amount and tax_amount > 0:
                invoice_doc["taxes"] = [
                    {
                        "charge_type": "Actual",
                        "account_head": "Tax - Company",  # Should be configured
                        "description": "Tax",
                        "tax_amount": tax_amount,
                    }
                ]

            # Create the document
            url = f"{self.url}/api/resource/Purchase Invoice"
            response = self.session.post(url, json=invoice_doc)
            response.raise_for_status()

            created_doc = response.json().get("data", {})

            logger.info(f"Created Purchase Invoice: {created_doc.get('name')}")

            return created_doc

        except Exception as e:
            logger.error(f"Error creating Purchase Invoice: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise

    def attach_file(
        self, doctype: str, docname: str, file_path: Path, file_name: Optional[str] = None
    ) -> dict:
        """
        Attach a file to an ERPNext document.

        Args:
            doctype: Document type (e.g., "Purchase Invoice")
            docname: Document name/ID
            file_path: Path to file to attach
            file_name: Optional custom file name

        Returns:
            File document
        """
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Read file content
            with open(file_path, "rb") as f:
                file_content = f.read()

            # Encode to base64
            file_b64 = base64.b64encode(file_content).decode("utf-8")

            # Prepare file document
            file_doc = {
                "doctype": "File",
                "file_name": file_name or file_path.name,
                "attached_to_doctype": doctype,
                "attached_to_name": docname,
                "is_private": 1,
                "content": file_b64,
            }

            # Create file
            url = f"{self.url}/api/resource/File"
            response = self.session.post(url, json=file_doc)
            response.raise_for_status()

            file_data = response.json().get("data", {})

            logger.info(f"Attached file {file_path.name} to {doctype} {docname}")

            return file_data

        except Exception as e:
            logger.error(f"Error attaching file: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise

    def get_document(self, doctype: str, docname: str) -> dict:
        """
        Get a document from ERPNext.

        Args:
            doctype: Document type
            docname: Document name/ID

        Returns:
            Document dictionary
        """
        try:
            url = f"{self.url}/api/resource/{doctype}/{docname}"
            response = self.session.get(url)
            response.raise_for_status()

            return response.json().get("data", {})

        except Exception as e:
            logger.error(f"Error getting document: {e}")
            raise
