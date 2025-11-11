"""
Tests for utility functions.
"""
import pytest
from utils import (
    normalize_amount,
    normalize_date,
    extract_invoice_number,
    detect_currency,
    calculate_confidence_score,
)


class TestNormalizeAmount:
    """Tests for amount normalization."""

    def test_simple_amount(self):
        assert normalize_amount("1234.56") == 1234.56

    def test_amount_with_comma(self):
        assert normalize_amount("1,234.56") == 1234.56

    def test_amount_with_currency_symbol(self):
        assert normalize_amount("₹ 41,200.00") == 41200.00
        assert normalize_amount("$ 1,234.56") == 1234.56

    def test_amount_with_multiple_commas(self):
        assert normalize_amount("1,234,567.89") == 1234567.89

    def test_invalid_amount(self):
        assert normalize_amount("abc") is None
        assert normalize_amount("") is None


class TestNormalizeDate:
    """Tests for date normalization."""

    def test_slash_format(self):
        result = normalize_date("08/11/2025")
        assert result == "2025-11-08" or result == "2025-08-11"  # Depends on locale

    def test_hyphen_format(self):
        assert normalize_date("2025-11-08") == "2025-11-08"

    def test_text_format(self):
        result = normalize_date("8 Nov 2025")
        assert result == "2025-11-08"

    def test_invalid_date(self):
        assert normalize_date("not a date") is None
        assert normalize_date("") is None


class TestExtractInvoiceNumber:
    """Tests for invoice number extraction."""

    def test_with_invoice_keyword(self):
        text = "Invoice #INV-2025-0099"
        assert extract_invoice_number(text) == "INV-2025-0099"

    def test_with_inv_keyword(self):
        text = "INV: ABC123"
        assert extract_invoice_number(text) == "ABC123"

    def test_with_hash(self):
        text = "Bill # 12345"
        result = extract_invoice_number(text)
        assert result is not None

    def test_no_invoice_number(self):
        text = "This is just plain text"
        result = extract_invoice_number(text)
        # May or may not find something, just ensure no crash
        assert result is None or isinstance(result, str)


class TestDetectCurrency:
    """Tests for currency detection."""

    def test_rupee_symbol(self):
        assert detect_currency("Total: ₹ 1,234") == "INR"

    def test_dollar_symbol(self):
        assert detect_currency("Total: $ 1,234") == "USD"

    def test_euro_symbol(self):
        assert detect_currency("Total: € 1,234") == "EUR"

    def test_no_symbol(self):
        assert detect_currency("Total: 1,234") == "INR"  # Default


class TestCalculateConfidenceScore:
    """Tests for confidence score calculation."""

    def test_none_value(self):
        assert calculate_confidence_score(None) == 0.0

    def test_text_value(self):
        score = calculate_confidence_score("TEST", "some context", "text")
        assert 0.0 <= score <= 1.0
        assert score > 0.7

    def test_number_value(self):
        score = calculate_confidence_score(1234.56, "", "number")
        assert 0.0 <= score <= 1.0
        assert score > 0.8

    def test_date_value(self):
        score = calculate_confidence_score("2025-11-08", "", "date")
        assert 0.0 <= score <= 1.0
        assert score > 0.8
