#!/usr/bin/env python3
"""
OCR-based Vendor Bill Ingestion for ERPNext.

Main application entry point with CLI interface.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Optional

import click

from config import config
from utils import load_image
from ocr_parsers import TesseractParser, GoogleVisionParser, FieldExtractor
from erpnext_client import ERPNextClient

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class InvoiceIngestion:
    """Main invoice ingestion orchestrator."""

    def __init__(
        self,
        erp_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        ocr_provider: Optional[str] = None,
    ):
        """
        Initialize invoice ingestion.

        Args:
            erp_url: ERPNext URL (uses config default if not provided)
            api_key: API key (uses config default if not provided)
            api_secret: API secret (uses config default if not provided)
            ocr_provider: OCR provider to use (tesseract or google_vision)
        """
        self.erp_client = ERPNextClient(erp_url, api_key, api_secret)
        self.field_extractor = FieldExtractor()

        # Initialize OCR parser
        provider = ocr_provider or config.OCR_PROVIDER

        if provider == "google_vision":
            self.ocr_parser = GoogleVisionParser()
            if not self.ocr_parser.is_available():
                logger.warning(
                    "Google Vision not available, falling back to Tesseract"
                )
                self.ocr_parser = TesseractParser()
        else:
            self.ocr_parser = TesseractParser()

        if not self.ocr_parser.is_available():
            raise RuntimeError("No OCR provider available")

        logger.info(f"Using OCR provider: {type(self.ocr_parser).__name__}")

    def process_invoice(
        self, file_path: Path, create_invoice: bool = True, attach_file: bool = True
    ) -> dict:
        """
        Process an invoice file end-to-end.

        Args:
            file_path: Path to invoice file (PDF/image)
            create_invoice: Whether to create Purchase Invoice in ERPNext
            attach_file: Whether to attach file to created invoice

        Returns:
            Result dictionary with extracted data and ERPNext status
        """
        result = {
            "file": str(file_path),
            "warnings": [],
            "errors": [],
        }

        try:
            # Step 1: Load images
            logger.info(f"Loading file: {file_path}")
            images = load_image(file_path)
            logger.info(f"Loaded {len(images)} page(s)")

            # Step 2: Perform OCR
            logger.info("Performing OCR...")
            ocr_results = self.ocr_parser.extract_text_from_multiple(images)

            # Combine text from all pages
            combined_text = "\n\n".join([r.text for r in ocr_results])
            avg_confidence = (
                sum([r.confidence for r in ocr_results]) / len(ocr_results)
                if ocr_results
                else 0.0
            )

            logger.info(f"OCR completed with average confidence: {avg_confidence:.2f}")

            if avg_confidence < 0.5:
                result["warnings"].append(
                    f"Low OCR confidence: {avg_confidence:.2f}"
                )

            # Step 3: Extract fields
            logger.info("Extracting invoice fields...")
            invoice_data = self.field_extractor.extract_fields(combined_text)

            # Convert to dict for result
            extracted_fields = self.field_extractor.to_dict(invoice_data)
            result.update(extracted_fields)

            # Step 4: Fuzzy vendor lookup
            if invoice_data.vendor_name.value:
                logger.info(f"Looking up vendor: {invoice_data.vendor_name.value}")
                best_match, suggestions = self.erp_client.fuzzy_match_vendor(
                    invoice_data.vendor_name.value
                )

                if best_match:
                    result["vendor_match"] = best_match.to_dict()
                    logger.info(f"Matched vendor: {best_match.name}")
                elif suggestions:
                    result["vendor_suggestions"] = [s.to_dict() for s in suggestions]
                    result["warnings"].append(
                        "No auto-approved vendor match. Manual selection required."
                    )
                    logger.warning("Vendor match requires manual approval")
                else:
                    result["errors"].append(
                        f"No vendor found matching: {invoice_data.vendor_name.value}"
                    )
                    logger.error("No vendor matches found")
            else:
                result["errors"].append("Could not extract vendor name from invoice")
                logger.error("Vendor name extraction failed")

            # Step 5: Create Purchase Invoice if requested and vendor matched
            if create_invoice and result.get("vendor_match"):
                logger.info("Creating Purchase Invoice in ERPNext...")

                try:
                    # Validate required fields
                    if not invoice_data.invoice_number.value:
                        raise ValueError("Invoice number is required")
                    if not invoice_data.invoice_date.value:
                        raise ValueError("Invoice date is required")
                    if not invoice_data.invoice_total.value:
                        raise ValueError("Invoice total is required")

                    # Create invoice
                    purchase_invoice = self.erp_client.create_purchase_invoice(
                        supplier=result["vendor_match"]["erp_id"],
                        invoice_number=invoice_data.invoice_number.value,
                        posting_date=invoice_data.invoice_date.value,
                        grand_total=invoice_data.invoice_total.value,
                        currency=invoice_data.currency,
                        tax_amount=invoice_data.tax_amount.value,
                        line_items=[
                            {
                                "description": item.description,
                                "qty": item.qty,
                                "unit_price": item.unit_price,
                                "line_total": item.line_total,
                            }
                            for item in invoice_data.line_items
                        ],
                    )

                    result["purchase_invoice_created"] = {
                        "docname": purchase_invoice.get("name"),
                        "status": "Draft",
                    }

                    logger.info(
                        f"Purchase Invoice created: {purchase_invoice.get('name')}"
                    )

                    # Step 6: Attach file if requested
                    if attach_file:
                        logger.info("Attaching invoice file...")
                        self.erp_client.attach_file(
                            doctype="Purchase Invoice",
                            docname=purchase_invoice.get("name"),
                            file_path=file_path,
                        )
                        logger.info("File attached successfully")

                except Exception as e:
                    error_msg = f"Failed to create Purchase Invoice: {str(e)}"
                    result["errors"].append(error_msg)
                    logger.error(error_msg)

            elif create_invoice:
                result["warnings"].append(
                    "Purchase Invoice not created (no vendor match or creation disabled)"
                )

        except Exception as e:
            error_msg = f"Processing failed: {str(e)}"
            result["errors"].append(error_msg)
            logger.exception(error_msg)

        return result


@click.command()
@click.option(
    "--file",
    "-f",
    "file_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to invoice file (PDF/image)",
)
@click.option(
    "--erp-url",
    help="ERPNext instance URL (uses .env if not provided)",
)
@click.option(
    "--api-key",
    help="ERPNext API key (uses .env if not provided)",
)
@click.option(
    "--api-secret",
    help="ERPNext API secret (uses .env if not provided)",
)
@click.option(
    "--ocr-provider",
    type=click.Choice(["tesseract", "google_vision"]),
    help="OCR provider to use (uses .env if not provided)",
)
@click.option(
    "--no-create",
    is_flag=True,
    help="Extract data only, don't create Purchase Invoice",
)
@click.option(
    "--no-attach",
    is_flag=True,
    help="Don't attach file to Purchase Invoice",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output JSON file path (prints to stdout if not provided)",
)
@click.option(
    "--pretty",
    is_flag=True,
    help="Pretty print JSON output",
)
def main(
    file_path: str,
    erp_url: Optional[str],
    api_key: Optional[str],
    api_secret: Optional[str],
    ocr_provider: Optional[str],
    no_create: bool,
    no_attach: bool,
    output: Optional[str],
    pretty: bool,
):
    """
    OCR-based Vendor Bill Ingestion for ERPNext.

    Process invoice files (PDF/images), extract vendor and invoice details,
    match vendors in ERPNext, and create draft Purchase Invoices.

    Example:

        python ocr_ingest.py --file invoice.pdf --erp-url https://erp.example.com
    """
    # Validate configuration if creating invoices
    if not no_create:
        validation_errors = config.validate()
        if validation_errors and not (erp_url and api_key and api_secret):
            logger.error("Configuration validation failed:")
            for error in validation_errors:
                logger.error(f"  - {error}")
            sys.exit(1)

    try:
        # Initialize ingestion
        ingestion = InvoiceIngestion(
            erp_url=erp_url,
            api_key=api_key,
            api_secret=api_secret,
            ocr_provider=ocr_provider,
        )

        # Process invoice
        result = ingestion.process_invoice(
            file_path=Path(file_path),
            create_invoice=not no_create,
            attach_file=not no_attach,
        )

        # Output result
        json_output = json.dumps(result, indent=2 if pretty else None)

        if output:
            with open(output, "w") as f:
                f.write(json_output)
            logger.info(f"Result written to: {output}")
        else:
            print(json_output)

        # Exit with error code if there were errors
        if result.get("errors"):
            sys.exit(1)

    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
