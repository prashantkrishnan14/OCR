"""
Tesseract OCR parser implementation.
"""
import logging
from typing import Optional
from PIL import Image
import pytesseract

from config import config
from utils import preprocess_image
from .base import OCRParser, OCRResult

logger = logging.getLogger(__name__)


class TesseractParser(OCRParser):
    """OCR parser using Tesseract engine."""

    def __init__(self):
        """Initialize Tesseract parser."""
        if config.TESSERACT_CMD:
            pytesseract.pytesseract.tesseract_cmd = config.TESSERACT_CMD

        # Verify Tesseract is available
        if not self.is_available():
            logger.warning("Tesseract is not available or not properly configured")

    def is_available(self) -> bool:
        """
        Check if Tesseract is available.

        Returns:
            True if Tesseract is installed and accessible
        """
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception as e:
            logger.error(f"Tesseract not available: {e}")
            return False

    def extract_text(self, image: Image.Image) -> OCRResult:
        """
        Extract text from image using Tesseract.

        Args:
            image: PIL Image to process

        Returns:
            OCRResult containing extracted text and confidence
        """
        try:
            # Preprocess image
            processed_image = preprocess_image(image)

            # Extract text with data
            data = pytesseract.image_to_data(
                processed_image, output_type=pytesseract.Output.DICT
            )

            # Extract text
            text = pytesseract.image_to_string(processed_image)

            # Calculate average confidence
            confidences = [
                int(conf) for conf in data["conf"] if conf != "-1" and str(conf).isdigit()
            ]

            avg_confidence = (
                sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
            )

            logger.info(f"Extracted {len(text)} characters with confidence {avg_confidence:.2f}")

            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence,
                metadata={
                    "engine": "tesseract",
                    "word_count": len(data["text"]),
                    "preprocessing": config.ENABLE_PREPROCESSING,
                },
            )

        except Exception as e:
            logger.error(f"Error during Tesseract OCR: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                metadata={"error": str(e), "engine": "tesseract"},
            )

    def extract_text_with_boxes(self, image: Image.Image) -> tuple[OCRResult, list[dict]]:
        """
        Extract text with bounding box information.

        Args:
            image: PIL Image to process

        Returns:
            Tuple of (OCRResult, list of box dictionaries)
        """
        try:
            processed_image = preprocess_image(image)

            # Get detailed data with bounding boxes
            data = pytesseract.image_to_data(
                processed_image, output_type=pytesseract.Output.DICT
            )

            # Extract text
            text = pytesseract.image_to_string(processed_image)

            # Calculate average confidence
            confidences = [
                int(conf) for conf in data["conf"] if conf != "-1" and str(conf).isdigit()
            ]
            avg_confidence = (
                sum(confidences) / len(confidences) / 100.0 if confidences else 0.0
            )

            # Build boxes list
            boxes = []
            n_boxes = len(data["text"])
            for i in range(n_boxes):
                if int(data["conf"][i]) > 0:
                    boxes.append(
                        {
                            "text": data["text"][i],
                            "left": data["left"][i],
                            "top": data["top"][i],
                            "width": data["width"][i],
                            "height": data["height"][i],
                            "confidence": int(data["conf"][i]) / 100.0,
                        }
                    )

            result = OCRResult(
                text=text.strip(),
                confidence=avg_confidence,
                metadata={"engine": "tesseract", "box_count": len(boxes)},
            )

            return result, boxes

        except Exception as e:
            logger.error(f"Error during Tesseract OCR with boxes: {e}")
            return (
                OCRResult(
                    text="", confidence=0.0, metadata={"error": str(e), "engine": "tesseract"}
                ),
                [],
            )
