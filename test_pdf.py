from pdf2image import convert_from_path
import os

# Set the path to Poppler
poppler_path = r'C:\Users\Rebaona\biometric_service\poppler-26.02.0\Library\bin'

# Test PDF path (change this to your PDF path)
pdf_path = r"C:\Users\Rebaona\Downloads\ID.jpeg"

try:
    print("Converting PDF...")
    images = convert_from_path(pdf_path, poppler_path=poppler_path, first_page=1, last_page=1)
    
    if images:
        print(f"SUCCESS! Converted {len(images)} page(s)")
        print(f"Image size: {images[0].size}")
    else:
        print("No images were converted")
        
except Exception as e:
    print(f"ERROR: {e}")