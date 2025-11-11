"""
Google Vision API OCR parser implementation.
"""
import logging
import os
from typing import Optional
from PIL import Image
import io

from config import config
from .base import OCRParser, OCRResult

logger = logging.getLogger(__name__)


class GoogleVisionParser(OCRParser):
    """OCR parser using Google Cloud Vision API."""

    def __init__(self):
        """Initialize Google Vision parser."""
        self.client = None

        if self.is_available():
            try:
                from google.cloud import vision

                self.client = vision.ImageAnnotatorClient()
                logger.info("Google Vision API client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Google Vision client: {e}")
                self.client = None

    def is_available(self) -> bool:
        """
        Check if Google Vision API is available.

        Returns:
            True if credentials are configured
        """
        if not config.GOOGLE_APPLICATION_CREDENTIALS:
            return False

        if not os.path.exists(config.GOOGLE_APPLICATION_CREDENTIALS):
            logger.warning(
                f"Google credentials file not found: {config.GOOGLE_APPLICATION_CREDENTIALS}"
            )
            return False

        try:
            from google.cloud import vision

            return True
        except ImportError:
            logger.warning("google-cloud-vision package not installed")
            return False

    def extract_text(self, image: Image.Image) -> OCRResult:
        """
        Extract text from image using Google Vision API.

        Args:
            image: PIL Image to process

        Returns:
            OCRResult containing extracted text and confidence
        """
        if not self.client:
            logger.error("Google Vision client not initialized")
            return OCRResult(
                text="",
                confidence=0.0,
                metadata={"error": "Client not initialized", "engine": "google_vision"},
            )

        try:
            from google.cloud import vision

            # Convert PIL Image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format="PNG")
            img_byte_arr = img_byte_arr.getvalue()

            # Create Vision API image object
            vision_image = vision.Image(content=img_byte_arr)

            # Perform text detection
            response = self.client.text_detection(image=vision_image)

            if response.error.message:
                raise Exception(f"API Error: {response.error.message}")

            texts = response.text_annotations

            if not texts:
                return OCRResult(
                    text="",
                    confidence=0.0,
                    metadata={"engine": "google_vision", "note": "No text detected"},
                )

            # First annotation contains full text
            full_text = texts[0].description

            # Calculate average confidence from all detections
            confidences = [text.confidence for text in response.full_text_annotation.pages[0].blocks if hasattr(text, 'confidence')]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.8

            logger.info(
                f"Extracted {len(full_text)} characters with confidence {avg_confidence:.2f}"
            )

            return OCRResult(
                text=full_text.strip(),
                confidence=avg_confidence,
                metadata={
                    "engine": "google_vision",
                    "detection_count": len(texts),
                },
            )

        except Exception as e:
            logger.error(f"Error during Google Vision OCR: {e}")
            return OCRResult(
                text="",
                confidence=0.0,
                metadata={"error": str(e), "engine": "google_vision"},
            )

    def extract_text_with_structure(self, image: Image.Image) -> tuple[OCRResult, dict]:
        """
        Extract text with document structure information.

        Args:
            image: PIL Image to process

        Returns:
            Tuple of (OCRResult, structure dictionary)
        """
        if not self.client:
            return (
                OCRResult(
                    text="",
                    confidence=0.0,
                    metadata={"error": "Client not initialized"},
                ),
                {},
            )

        try:
            from google.cloud import vision

            # Convert PIL Image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format="PNG")
            img_byte_arr = img_byte_arr.getvalue()

            # Create Vision API image object
            vision_image = vision.Image(content=img_byte_arr)

            # Perform document text detection (better for structured documents)
            response = self.client.document_text_detection(image=vision_image)

            if response.error.message:
                raise Exception(f"API Error: {response.error.message}")

            document = response.full_text_annotation
            full_text = document.text

            # Extract structure
            structure = {
                "pages": len(document.pages),
                "blocks": [],
                "paragraphs": [],
                "words": [],
            }

            for page in document.pages:
                for block in page.blocks:
                    structure["blocks"].append(
                        {
                            "confidence": block.confidence,
                            "text": self._get_block_text(block),
                        }
                    )

                    for paragraph in block.paragraphs:
                        structure["paragraphs"].append(
                            {
                                "confidence": paragraph.confidence,
                                "text": self._get_paragraph_text(paragraph),
                            }
                        )

            avg_confidence = (
                sum([b["confidence"] for b in structure["blocks"]])
                / len(structure["blocks"])
                if structure["blocks"]
                else 0.0
            )

            result = OCRResult(
                text=full_text.strip(),
                confidence=avg_confidence,
                metadata={
                    "engine": "google_vision",
                    "document_structure": True,
                },
            )

            return result, structure

        except Exception as e:
            logger.error(f"Error during Google Vision document OCR: {e}")
            return (
                OCRResult(text="", confidence=0.0, metadata={"error": str(e)}),
                {},
            )

    @staticmethod
    def _get_block_text(block) -> str:
        """Extract text from a block."""
        text = ""
        for paragraph in block.paragraphs:
            for word in paragraph.words:
                word_text = "".join([symbol.text for symbol in word.symbols])
                text += word_text + " "
        return text.strip()

    @staticmethod
    def _get_paragraph_text(paragraph) -> str:
        """Extract text from a paragraph."""
        text = ""
        for word in paragraph.words:
            word_text = "".join([symbol.text for symbol in word.symbols])
            text += word_text + " "
        return text.strip()
