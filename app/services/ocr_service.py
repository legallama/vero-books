import time
from decimal import Decimal
from datetime import date
import random

class OCRService:
    @staticmethod
    def scan_receipt(file_path):
        """
        Simulates an AI-powered OCR scan of a receipt image.
        In a real-world scenario, this would call AWS Textract, Google Vision, or Tesseract.
        """
        # Simulate 'AI' processing time
        time.sleep(2.5)
        
        # Mocking extraction based on random common vendors
        vendors = [
            {"name": "Starbucks", "amount": "4.75", "category": "Meals & Entertainment"},
            {"name": "Amazon.com", "amount": "124.50", "category": "Office Supplies"},
            {"name": "Shell Gas", "amount": "45.00", "category": "Travel"},
            {"name": "Home Depot", "amount": "210.99", "category": "Repairs & Maintenance"},
            {"name": "Staples", "amount": "12.40", "category": "Office Supplies"}
        ]
        
        extracted = random.choice(vendors)
        
        return {
            "vendor_name": extracted["name"],
            "amount": extracted["amount"],
            "date": date.today().strftime('%Y-%m-%d'),
            "category_suggestion": extracted["category"],
            "confidence_score": round(random.uniform(0.92, 0.99), 2)
        }
