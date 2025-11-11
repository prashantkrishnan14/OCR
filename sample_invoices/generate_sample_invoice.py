#!/usr/bin/env python3
"""
Generate a sample invoice image for testing OCR ingestion.
"""
from PIL import Image, ImageDraw, ImageFont
import sys


def generate_invoice_image(output_path: str = "sample_invoice.png"):
    """Generate a sample invoice image."""

    # Invoice text
    invoice_text = """ACME SUPPLIES PVT LTD
123 Business Park, Electronic City
Bangalore, Karnataka 560100
GSTIN: 29AABCT1234C1Z5

                        TAX INVOICE

Invoice Number: INV-2025-0099
Invoice Date: 08/11/2025
Due Date: 08/12/2025

Bill To:
Tech Solutions Ltd
456 Innovation Street
Bangalore, Karnataka 560001

Description                      Qty    Rate        Amount
----------------------------------------------------------------
Cable ties 100mm (Pack of 100)    10    150.00     1,500.00
Zip ties 200mm (Pack of 50)       20  1,250.00    25,000.00
Wire management clips              5    340.00     1,700.00
Cable tray 2m length              15    620.00     9,300.00
Cable glands M20                  30    126.67     3,800.00

                                         Subtotal: 41,300.00

                                         CGST @ 9%:  3,717.00
                                         SGST @ 9%:  3,717.00

                                    TOTAL AMOUNT: ₹ 48,734.00

Payment Terms: Net 30 Days
Bank Details:
  HDFC Bank Ltd
  Account: 12345678901234
  IFSC: HDFC0001234

Authorized Signatory

For ACME SUPPLIES PVT LTD"""

    # Create image
    width, height = 2480, 3508  # A4 at 300 DPI
    image = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(image)

    # Use default font (try to use a better font if available)
    try:
        # Try to use a monospace font for better formatting
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 40)
        font_normal = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 32)
    except:
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/Courier.dfont", 40)
            font_normal = ImageFont.truetype("/System/Library/Fonts/Courier.dfont", 32)
        except:
            # Fallback to default
            font_large = ImageFont.load_default()
            font_normal = ImageFont.load_default()

    # Draw text
    y_position = 100
    for line in invoice_text.split('\n'):
        draw.text((100, y_position), line, fill='black', font=font_normal)
        y_position += 50

    # Add a border
    draw.rectangle([(50, 50), (width-50, height-50)], outline='black', width=3)

    # Save
    image.save(output_path, 'PNG', dpi=(300, 300))
    print(f"Sample invoice generated: {output_path}")


if __name__ == "__main__":
    output = sys.argv[1] if len(sys.argv) > 1 else "sample_invoice.png"
    generate_invoice_image(output)
