#!/usr/bin/env python3
"""
Demo script to test OCR extraction without ERPNext connection.

This script extracts data from an invoice without creating a Purchase Invoice,
useful for testing OCR accuracy without needing ERPNext credentials.
"""
import json
import sys
from pathlib import Path

from utils import load_image
from ocr_parsers import TesseractParser, FieldExtractor


def demo_extract(invoice_path: str):
    """
    Demonstrate OCR extraction without ERPNext.

    Args:
        invoice_path: Path to invoice file
    """
    print(f"Processing invoice: {invoice_path}")
    print("-" * 60)

    # Load images
    print("\n1. Loading file...")
    images = load_image(invoice_path)
    print(f"   Loaded {len(images)} page(s)")

    # Initialize OCR parser
    print("\n2. Initializing OCR parser...")
    parser = TesseractParser()

    if not parser.is_available():
        print("   ERROR: Tesseract not available!")
        print("   Please install Tesseract OCR:")
        print("     - Ubuntu: sudo apt-get install tesseract-ocr")
        print("     - macOS: brew install tesseract")
        print("     - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        sys.exit(1)

    print("   Tesseract is available")

    # Perform OCR
    print("\n3. Performing OCR...")
    ocr_results = parser.extract_text_from_multiple(images)

    # Display OCR results
    for i, result in enumerate(ocr_results):
        print(f"\n   Page {i + 1}:")
        print(f"   - Extracted {len(result.text)} characters")
        print(f"   - Confidence: {result.confidence:.2%}")

    # Combine text
    combined_text = "\n\n".join([r.text for r in ocr_results])

    # Display extracted text
    print("\n4. Extracted Text:")
    print("-" * 60)
    print(combined_text[:500])  # Show first 500 chars
    if len(combined_text) > 500:
        print(f"... ({len(combined_text) - 500} more characters)")
    print("-" * 60)

    # Extract fields
    print("\n5. Extracting fields...")
    extractor = FieldExtractor()
    invoice_data = extractor.extract_fields(combined_text)

    # Display extracted fields
    print("\n6. Extracted Fields:")
    print("-" * 60)

    fields = extractor.to_dict(invoice_data)

    print(f"\nVendor Name:")
    print(f"  Value: {fields['vendor_name']['value']}")
    print(f"  Confidence: {fields['vendor_name']['confidence']:.2%}")

    print(f"\nInvoice Number:")
    print(f"  Value: {fields['invoice_number']['value']}")
    print(f"  Confidence: {fields['invoice_number']['confidence']:.2%}")

    print(f"\nInvoice Date:")
    print(f"  Value: {fields['invoice_date']['value']}")
    print(f"  Confidence: {fields['invoice_date']['confidence']:.2%}")

    print(f"\nInvoice Total:")
    print(f"  Value: {fields['invoice_total']['value']} {fields['invoice_total']['currency']}")
    print(f"  Confidence: {fields['invoice_total']['confidence']:.2%}")

    print(f"\nTax Amount:")
    print(f"  Value: {fields['tax_amount']['value']} {fields['tax_amount']['currency']}")
    print(f"  Confidence: {fields['tax_amount']['confidence']:.2%}")

    print(f"\nLine Items: {len(fields['line_items'])} found")
    for i, item in enumerate(fields['line_items'][:3], 1):  # Show first 3
        print(f"  {i}. {item['description']}")
        print(f"     Qty: {item['qty']}, Price: {item['unit_price']}, Total: {item['line_total']}")

    # Save full result to JSON
    output_file = Path(invoice_path).stem + "_extracted.json"
    with open(output_file, "w") as f:
        json.dump(fields, f, indent=2)

    print(f"\n7. Full results saved to: {output_file}")
    print("-" * 60)
    print("\nDemo completed successfully!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python demo_extract_only.py <invoice_file>")
        print("\nExample:")
        print("  python demo_extract_only.py sample_invoices/sample_invoice.pdf")
        sys.exit(1)

    invoice_path = sys.argv[1]

    if not Path(invoice_path).exists():
        print(f"Error: File not found: {invoice_path}")
        sys.exit(1)

    try:
        demo_extract(invoice_path)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
