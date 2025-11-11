"""
Base OCR parser interface and result classes.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Any
from PIL import Image


@dataclass
class OCRResult:
    """Container for OCR extraction results."""

    text: str
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure confidence is between 0 and 1."""
        self.confidence = max(0.0, min(1.0, self.confidence))


class OCRParser(ABC):
    """Abstract base class for OCR parsers."""

    @abstractmethod
    def extract_text(self, image: Image.Image) -> OCRResult:
        """
        Extract text from an image.

        Args:
            image: PIL Image to process

        Returns:
            OCRResult containing extracted text and confidence
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the OCR provider is available.

        Returns:
            True if provider is configured and ready
        """
        pass

    def extract_text_from_multiple(self, images: list[Image.Image]) -> list[OCRResult]:
        """
        Extract text from multiple images.

        Args:
            images: List of PIL Images

        Returns:
            List of OCRResult objects
        """
        results = []
        for idx, image in enumerate(images):
            result = self.extract_text(image)
            result.metadata["page_number"] = idx + 1
            results.append(result)

        return results
