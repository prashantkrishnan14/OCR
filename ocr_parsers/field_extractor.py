"""
Field extraction logic for parsing invoice data from OCR text.
"""
import re
import logging
from typing import Optional
from dataclasses import dataclass, field

from config import config
from utils import (
    extract_invoice_number,
    extract_dates,
    extract_amounts,
    normalize_date,
    normalize_amount,
    detect_currency,
    calculate_confidence_score,
    clean_text,
)

logger = logging.getLogger(__name__)


@dataclass
class ExtractedField:
    """Container for an extracted field with confidence."""

    value: any
    confidence: float = 0.0
    raw_text: str = ""


@dataclass
class LineItem:
    """Represents a line item from an invoice."""

    description: str
    qty: float = 0.0
    unit_price: float = 0.0
    line_total: float = 0.0
    confidence: float = 0.0


@dataclass
class InvoiceData:
    """Container for all extracted invoice data."""

    vendor_name: ExtractedField = field(default_factory=lambda: ExtractedField(None))
    invoice_number: ExtractedField = field(default_factory=lambda: ExtractedField(None))
    invoice_date: ExtractedField = field(default_factory=lambda: ExtractedField(None))
    invoice_total: ExtractedField = field(default_factory=lambda: ExtractedField(None))
    tax_amount: ExtractedField = field(default_factory=lambda: ExtractedField(None))
    currency: str = "INR"
    line_items: list[LineItem] = field(default_factory=list)


class FieldExtractor:
    """Extracts structured fields from OCR text."""

    def __init__(self):
        """Initialize field extractor."""
        pass

    def extract_fields(self, ocr_text: str) -> InvoiceData:
        """
        Extract all invoice fields from OCR text.

        Args:
            ocr_text: Raw OCR text from invoice

        Returns:
            InvoiceData object with extracted fields
        """
        cleaned_text = clean_text(ocr_text)
        invoice_data = InvoiceData()

        # Extract currency first
        invoice_data.currency = detect_currency(cleaned_text)

        # Extract invoice number
        invoice_data.invoice_number = self._extract_invoice_number(cleaned_text)

        # Extract dates
        invoice_data.invoice_date = self._extract_invoice_date(cleaned_text)

        # Extract amounts
        invoice_data.invoice_total, invoice_data.tax_amount = self._extract_amounts(
            cleaned_text
        )

        # Extract vendor name
        invoice_data.vendor_name = self._extract_vendor_name(cleaned_text)

        # Extract line items
        invoice_data.line_items = self._extract_line_items(cleaned_text)

        logger.info(f"Extracted invoice data: {invoice_data.invoice_number.value}")

        return invoice_data

    def _extract_invoice_number(self, text: str) -> ExtractedField:
        """Extract invoice number from text."""
        inv_num = extract_invoice_number(text)

        if inv_num:
            confidence = calculate_confidence_score(inv_num, text, "text")
            return ExtractedField(value=inv_num, confidence=confidence, raw_text=inv_num)

        return ExtractedField(value=None, confidence=0.0)

    def _extract_invoice_date(self, text: str) -> ExtractedField:
        """Extract invoice date from text."""
        dates = extract_dates(text)

        if dates:
            # Take the first valid date (typically invoice date appears early)
            for date_str in dates:
                normalized = normalize_date(date_str)
                if normalized:
                    confidence = calculate_confidence_score(normalized, text, "date")
                    return ExtractedField(
                        value=normalized, confidence=confidence, raw_text=date_str
                    )

        return ExtractedField(value=None, confidence=0.0)

    def _extract_amounts(self, text: str) -> tuple[ExtractedField, ExtractedField]:
        """
        Extract invoice total and tax amount.

        Returns:
            Tuple of (invoice_total, tax_amount)
        """
        lines = text.split("\n")

        # Look for total amount
        total_amount = None
        tax_amount = None

        for i, line in enumerate(lines):
            line_lower = line.lower()

            # Check for total keywords
            if any(
                keyword in line_lower
                for keyword in ["total", "grand total", "amount due", "balance"]
            ):
                amounts = extract_amounts(line)
                if amounts:
                    total_amount = max(amounts)  # Take the largest amount

            # Check for tax keywords
            if any(keyword in line_lower for keyword in config.TAX_KEYWORDS):
                amounts = extract_amounts(line)
                if amounts:
                    tax_amount = amounts[0]  # Take first tax amount found

        # Build ExtractedField objects
        total_field = ExtractedField(value=None, confidence=0.0)
        tax_field = ExtractedField(value=None, confidence=0.0)

        if total_amount:
            total_field = ExtractedField(
                value=total_amount,
                confidence=calculate_confidence_score(total_amount, text, "number"),
                raw_text=str(total_amount),
            )

        if tax_amount:
            tax_field = ExtractedField(
                value=tax_amount,
                confidence=calculate_confidence_score(tax_amount, text, "number"),
                raw_text=str(tax_amount),
            )

        # If tax not found but total is, estimate tax as ~18% if reasonable
        if total_amount and not tax_amount:
            estimated_tax = total_amount * 0.15  # Rough estimate
            if 0 < estimated_tax < total_amount:
                logger.info(f"Estimated tax amount: {estimated_tax}")

        return total_field, tax_field

    def _extract_vendor_name(self, text: str) -> ExtractedField:
        """
        Extract vendor/supplier name from text.

        Typically appears at the top of the invoice.
        """
        lines = text.split("\n")

        # Look in first 10 lines for company name
        # Usually in all caps or title case with keywords like "Ltd", "Inc", "Pvt"
        for line in lines[:10]:
            line_stripped = line.strip()

            # Skip if line is too short or contains common header keywords
            if len(line_stripped) < 3:
                continue

            if any(
                keyword in line_stripped.lower()
                for keyword in ["invoice", "bill", "tax", "date", "number"]
            ):
                continue

            # Check for company indicators
            if any(
                indicator in line_stripped
                for indicator in ["Ltd", "LTD", "Inc", "INC", "Pvt", "PVT", "LLC", "Corp"]
            ):
                confidence = calculate_confidence_score(line_stripped, text, "text")
                return ExtractedField(
                    value=line_stripped, confidence=confidence, raw_text=line_stripped
                )

            # Check if line is mostly uppercase (common for company names)
            if line_stripped.isupper() and len(line_stripped) > 5:
                confidence = calculate_confidence_score(line_stripped, text, "text")
                return ExtractedField(
                    value=line_stripped, confidence=confidence, raw_text=line_stripped
                )

        # Fallback: take first substantial line
        for line in lines[:5]:
            line_stripped = line.strip()
            if len(line_stripped) > 5:
                confidence = 0.5  # Lower confidence for fallback
                return ExtractedField(
                    value=line_stripped, confidence=confidence, raw_text=line_stripped
                )

        return ExtractedField(value=None, confidence=0.0)

    def _extract_line_items(self, text: str) -> list[LineItem]:
        """
        Extract line items from invoice text.

        This is a best-effort heuristic approach.
        """
        lines = text.split("\n")
        line_items = []

        # Pattern to match line items: description followed by numbers
        # Example: "Cable ties 100mm    10    150.00    1500.00"
        item_pattern = re.compile(
            r"^([A-Za-z][A-Za-z0-9\s\-,]+?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:[,\.]\d+)*)\s+(\d+(?:[,\.]\d+)*)$"
        )

        for line in lines:
            line = line.strip()

            # Skip header lines
            if any(
                keyword in line.lower()
                for keyword in [
                    "description",
                    "item",
                    "quantity",
                    "qty",
                    "price",
                    "amount",
                    "total",
                ]
            ):
                continue

            match = item_pattern.match(line)
            if match:
                description = match.group(1).strip()
                qty = float(match.group(2))
                unit_price = normalize_amount(match.group(3)) or 0.0
                line_total = normalize_amount(match.group(4)) or 0.0

                # Validation: line_total should approximately equal qty * unit_price
                expected_total = qty * unit_price
                if abs(line_total - expected_total) / max(line_total, 1) < 0.1:
                    line_items.append(
                        LineItem(
                            description=description,
                            qty=qty,
                            unit_price=unit_price,
                            line_total=line_total,
                            confidence=0.75,
                        )
                    )

        # If no structured line items found, create a fallback single line item
        if not line_items:
            logger.warning("Could not extract structured line items, using fallback")

        return line_items

    def to_dict(self, invoice_data: InvoiceData) -> dict:
        """
        Convert InvoiceData to dictionary format for JSON output.

        Args:
            invoice_data: InvoiceData object

        Returns:
            Dictionary representation
        """
        return {
            "vendor_name": {
                "value": invoice_data.vendor_name.value,
                "confidence": round(invoice_data.vendor_name.confidence, 2),
            },
            "invoice_number": {
                "value": invoice_data.invoice_number.value,
                "confidence": round(invoice_data.invoice_number.confidence, 2),
            },
            "invoice_date": {
                "value": invoice_data.invoice_date.value,
                "confidence": round(invoice_data.invoice_date.confidence, 2),
            },
            "invoice_total": {
                "value": invoice_data.invoice_total.value,
                "currency": invoice_data.currency,
                "confidence": round(invoice_data.invoice_total.confidence, 2),
            },
            "tax_amount": {
                "value": invoice_data.tax_amount.value,
                "currency": invoice_data.currency,
                "confidence": round(invoice_data.tax_amount.confidence, 2),
            },
            "line_items": [
                {
                    "description": item.description,
                    "qty": item.qty,
                    "unit_price": item.unit_price,
                    "line_total": item.line_total,
                    "confidence": round(item.confidence, 2),
                }
                for item in invoice_data.line_items
            ],
        }
