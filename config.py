"""
Configuration module for OCR Vendor Bill Ingestion.
Loads settings from environment variables with sensible defaults.
"""
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for OCR ingestion system."""

    # ERPNext Configuration
    ERPNEXT_URL: str = os.getenv("ERPNEXT_URL", "")
    ERPNEXT_API_KEY: str = os.getenv("ERPNEXT_API_KEY", "")
    ERPNEXT_API_SECRET: str = os.getenv("ERPNEXT_API_SECRET", "")

    # OCR Configuration
    TESSERACT_CMD: Optional[str] = os.getenv("TESSERACT_CMD")
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = os.getenv(
        "GOOGLE_APPLICATION_CREDENTIALS"
    )
    OCR_PROVIDER: str = os.getenv("OCR_PROVIDER", "tesseract")

    # Fuzzy Matching Thresholds
    VENDOR_MATCH_THRESHOLD: int = int(os.getenv("VENDOR_MATCH_THRESHOLD", "75"))
    VENDOR_AUTO_APPROVE_THRESHOLD: int = int(
        os.getenv("VENDOR_AUTO_APPROVE_THRESHOLD", "85")
    )

    # Image Preprocessing
    ENABLE_PREPROCESSING: bool = os.getenv("ENABLE_PREPROCESSING", "true").lower() == "true"
    DESKEW_ENABLED: bool = os.getenv("DESKEW_ENABLED", "true").lower() == "true"
    DENOISE_ENABLED: bool = os.getenv("DENOISE_ENABLED", "true").lower() == "true"

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Supported file formats
    SUPPORTED_IMAGE_FORMATS = {".jpg", ".jpeg", ".png", ".tiff", ".tif", ".bmp"}
    SUPPORTED_FORMATS = SUPPORTED_IMAGE_FORMATS | {".pdf"}

    # Regex patterns for extraction
    INVOICE_NUMBER_PATTERNS = [
        r"(?:invoice|inv|bill)[\s#:.-]*([A-Z0-9-]+)",
        r"(?:reference|ref)[\s#:.-]*([A-Z0-9-]+)",
        r"#\s*([A-Z0-9-]+)",
    ]

    DATE_PATTERNS = [
        r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b",
        r"\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b",
        r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b",
    ]

    AMOUNT_PATTERNS = [
        r"(?:total|amount|grand\s+total|balance\s+due)[\s:]*[\$₹€£]?\s*([\d,]+\.?\d*)",
        r"[\$₹€£]\s*([\d,]+\.?\d*)",
    ]

    TAX_KEYWORDS = [
        "gst",
        "vat",
        "tax",
        "igst",
        "cgst",
        "sgst",
        "service tax",
        "sales tax",
    ]

    CURRENCY_SYMBOLS = {"₹": "INR", "$": "USD", "€": "EUR", "£": "GBP"}

    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration settings."""
        errors = []

        if not cls.ERPNEXT_URL:
            errors.append("ERPNEXT_URL is required")

        if not cls.ERPNEXT_API_KEY or not cls.ERPNEXT_API_SECRET:
            errors.append("ERPNEXT_API_KEY and ERPNEXT_API_SECRET are required")

        if cls.OCR_PROVIDER not in ["tesseract", "google_vision"]:
            errors.append("OCR_PROVIDER must be 'tesseract' or 'google_vision'")

        if cls.OCR_PROVIDER == "google_vision" and not cls.GOOGLE_APPLICATION_CREDENTIALS:
            errors.append(
                "GOOGLE_APPLICATION_CREDENTIALS required for google_vision provider"
            )

        return errors


# Export singleton instance
config = Config()
