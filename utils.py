"""
Utility functions for image preprocessing, text normalization, and helpers.
"""
import re
import logging
from typing import Optional, Union
from pathlib import Path
from datetime import datetime

import cv2
import numpy as np
from PIL import Image
from pdf2image import convert_from_path
from dateutil import parser as date_parser

from config import config

logger = logging.getLogger(__name__)


def preprocess_image(image: Union[np.ndarray, Image.Image]) -> Image.Image:
    """
    Preprocess image for better OCR results.

    Args:
        image: Input image as numpy array or PIL Image

    Returns:
        Preprocessed PIL Image
    """
    if not config.ENABLE_PREPROCESSING:
        if isinstance(image, np.ndarray):
            return Image.fromarray(image)
        return image

    # Convert PIL to OpenCV if needed
    if isinstance(image, Image.Image):
        img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    else:
        img = image

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Denoise
    if config.DENOISE_ENABLED:
        gray = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

    # Deskew
    if config.DESKEW_ENABLED:
        gray = deskew_image(gray)

    # Threshold to binary
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

    # Convert back to PIL
    return Image.fromarray(gray)


def deskew_image(image: np.ndarray) -> np.ndarray:
    """
    Deskew an image by detecting text angle.

    Args:
        image: Grayscale image as numpy array

    Returns:
        Deskewed image
    """
    coords = np.column_stack(np.where(image > 0))
    if len(coords) == 0:
        return image

    angle = cv2.minAreaRect(coords)[-1]

    # Correct angle
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    # Rotate only if angle is significant
    if abs(angle) < 0.5:
        return image

    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(
        image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )

    return rotated


def convert_pdf_to_images(pdf_path: Union[str, Path]) -> list[Image.Image]:
    """
    Convert PDF pages to PIL Images.

    Args:
        pdf_path: Path to PDF file

    Returns:
        List of PIL Images (one per page)
    """
    try:
        images = convert_from_path(str(pdf_path), dpi=300)
        logger.info(f"Converted {len(images)} pages from PDF: {pdf_path}")
        return images
    except Exception as e:
        logger.error(f"Error converting PDF to images: {e}")
        raise


def load_image(file_path: Union[str, Path]) -> list[Image.Image]:
    """
    Load image(s) from file. Handles both images and PDFs.

    Args:
        file_path: Path to image or PDF file

    Returns:
        List of PIL Images
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    suffix = path.suffix.lower()

    if suffix not in config.SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported file format: {suffix}. "
            f"Supported: {config.SUPPORTED_FORMATS}"
        )

    if suffix == ".pdf":
        return convert_pdf_to_images(path)
    else:
        return [Image.open(path)]


def normalize_amount(amount_str: str) -> Optional[float]:
    """
    Normalize amount string to float.

    Args:
        amount_str: String containing amount (e.g., "₹ 41,200.00")

    Returns:
        Float value or None if parsing fails
    """
    if not amount_str:
        return None

    # Remove currency symbols and whitespace
    cleaned = re.sub(r"[^\d,.-]", "", amount_str)

    # Handle thousands separators
    # Assume comma is thousands separator if there are multiple or if format is X,XXX.XX
    if "," in cleaned:
        parts = cleaned.split(".")
        if len(parts) == 2:
            # Format like 1,234.56
            cleaned = parts[0].replace(",", "") + "." + parts[1]
        else:
            # Format like 1,234 or 1,234,567
            cleaned = cleaned.replace(",", "")

    try:
        return float(cleaned)
    except ValueError:
        logger.warning(f"Could not parse amount: {amount_str}")
        return None


def detect_currency(text: str) -> str:
    """
    Detect currency from text based on symbols.

    Args:
        text: Text containing potential currency symbols

    Returns:
        ISO currency code (e.g., "INR", "USD")
    """
    for symbol, code in config.CURRENCY_SYMBOLS.items():
        if symbol in text:
            return code

    # Default to INR if not detected
    return "INR"


def normalize_date(date_str: str) -> Optional[str]:
    """
    Parse and normalize date string to ISO format (yyyy-mm-dd).

    Args:
        date_str: Date string in various formats

    Returns:
        ISO formatted date string or None if parsing fails
    """
    if not date_str:
        return None

    try:
        # Use dateutil parser for flexible parsing
        parsed_date = date_parser.parse(date_str, fuzzy=True, dayfirst=True)
        return parsed_date.strftime("%Y-%m-%d")
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not parse date: {date_str} - {e}")
        return None


def extract_invoice_number(text: str) -> Optional[str]:
    """
    Extract invoice number from text using regex patterns.

    Args:
        text: OCR extracted text

    Returns:
        Invoice number or None
    """
    text_lower = text.lower()

    for pattern in config.INVOICE_NUMBER_PATTERNS:
        matches = re.finditer(pattern, text_lower, re.IGNORECASE)
        for match in matches:
            inv_num = match.group(1).strip().upper()
            if len(inv_num) >= 3:  # Minimum length check
                return inv_num

    return None


def extract_dates(text: str) -> list[str]:
    """
    Extract all potential dates from text.

    Args:
        text: OCR extracted text

    Returns:
        List of date strings
    """
    dates = []

    for pattern in config.DATE_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        dates.extend(matches)

    return dates


def extract_amounts(text: str) -> list[float]:
    """
    Extract all potential monetary amounts from text.

    Args:
        text: OCR extracted text

    Returns:
        List of float amounts
    """
    amounts = []

    for pattern in config.AMOUNT_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            amount = normalize_amount(match)
            if amount:
                amounts.append(amount)

    return amounts


def calculate_confidence_score(
    extracted_value: any, context: str = "", value_type: str = "text"
) -> float:
    """
    Calculate confidence score for extracted value.

    Args:
        extracted_value: The extracted value
        context: Context text where value was found
        value_type: Type of value (text, number, date)

    Returns:
        Confidence score between 0.0 and 1.0
    """
    if extracted_value is None:
        return 0.0

    base_confidence = 0.7

    # Increase confidence based on value characteristics
    if value_type == "text" and isinstance(extracted_value, str):
        if len(extracted_value) > 3:
            base_confidence += 0.1
        if extracted_value.isupper():
            base_confidence += 0.05

    elif value_type == "number" and isinstance(extracted_value, (int, float)):
        if extracted_value > 0:
            base_confidence += 0.15

    elif value_type == "date":
        if extracted_value:
            base_confidence += 0.15

    # Context boost
    if context and len(context) > 10:
        base_confidence += 0.05

    return min(base_confidence, 1.0)


def clean_text(text: str) -> str:
    """
    Clean OCR text by removing extra whitespace and artifacts.

    Args:
        text: Raw OCR text

    Returns:
        Cleaned text
    """
    # Remove multiple spaces
    text = re.sub(r"\s+", " ", text)

    # Remove common OCR artifacts
    text = re.sub(r"[|~`]", "", text)

    return text.strip()
