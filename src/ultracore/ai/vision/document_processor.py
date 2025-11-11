"""
UltraCore Vision AI - Australian Document Processing
Handles invoices, receipts, bank statements, ATO documents
"""

from openai import OpenAI
import base64
from typing import Dict, List, Any, Optional
from decimal import Decimal
from datetime import datetime
import re
import json

class AustralianDocumentProcessor:
    """Process Australian financial documents with GPT-4 Vision"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        
        # Australian-specific patterns
        self.abn_pattern = r'\b\d{2}\s?\d{3}\s?\d{3}\s?\d{3}\b'  # ABN format
        self.bsb_pattern = r'\b\d{3}-?\d{3}\b'  # BSB format
        self.tfn_pattern = r'\b\d{3}\s?\d{3}\s?\d{3}\b'  # TFN format (handle carefully)
        
    async def process_invoice(self, image_path: str) -> Dict[str, Any]:
        """Extract data from Australian invoices"""
        
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        response = self.client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Extract the following from this Australian invoice:
                        - ABN (Australian Business Number)
                        - Business name
                        - Invoice number
                        - Date
                        - Total amount (including GST)
                        - GST amount
                        - Payment terms
                        - Due date
                        - BPAY reference (if present)
                        - Bank details (BSB and account)
                        Return as JSON."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }],
            max_tokens=1000
        )
        
        # Parse response
        content = response.choices[0].message.content
        invoice_data = json.loads(content)
        
        # Add to data mesh
        await self.send_to_data_mesh({
            "domain": "invoice_processing",
            "data": invoice_data,
            "timestamp": datetime.now().isoformat(),
            "compliance": self.check_compliance(invoice_data)
        })
        
        return invoice_data
    
    async def process_bank_statement(self, image_path: str) -> Dict[str, Any]:
        """Process Australian bank statements"""
        
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        response = self.client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Extract from this Australian bank statement:
                        - Bank name
                        - Account holder
                        - BSB and account number
                        - Statement period
                        - Opening balance
                        - Closing balance
                        - All transactions (date, description, amount, balance)
                        - Interest earned
                        - Fees charged
                        Format as structured JSON."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }],
            max_tokens=2000
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def process_ato_document(self, image_path: str) -> Dict[str, Any]:
        """Process Australian Tax Office documents"""
        
        # Special handling for tax documents
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        response = self.client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Extract from this ATO document:
                        - Document type (PAYG summary, tax assessment, etc.)
                        - Tax file number (mask all but last 3 digits)
                        - Financial year
                        - Taxable income
                        - Tax withheld
                        - Medicare levy
                        - Any refund or debt amount
                        IMPORTANT: Mask sensitive information appropriately."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }],
            max_tokens=1000
        )
        
        data = json.loads(response.choices[0].message.content)
        
        # Secure sensitive data
        if 'tfn' in data:
            data['tfn'] = f"***{data['tfn'][-3:]}"
        
        return data
    
    def check_compliance(self, data: Dict) -> Dict[str, bool]:
        """Check Australian compliance requirements"""
        return {
            "has_abn": bool(re.search(self.abn_pattern, str(data))),
            "has_gst": 'gst' in str(data).lower(),
            "valid_bsb": bool(re.search(self.bsb_pattern, str(data))),
            "aml_ctf_check": True  # Would integrate with AUSTRAC
        }
    
    async def send_to_data_mesh(self, data: Dict):
        """Send to data mesh for ML processing"""
        # Integration with your data mesh
        pass


class SmartReceiptScanner:
    """Scan and categorize receipts for tax purposes"""
    
    def __init__(self, client: OpenAI):
        self.client = client
        self.tax_categories = {
            "business": ["office supplies", "software", "equipment"],
            "medical": ["pharmacy", "doctor", "hospital"],
            "education": ["course", "training", "books"],
            "charity": ["donation", "charity", "fundraiser"]
        }
    
    async def scan_receipt(self, image_path: str) -> Dict[str, Any]:
        """Scan receipt and categorize for Australian tax"""
        
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        response = self.client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """Extract from this receipt:
                        - Store name and ABN
                        - Date
                        - Total amount
                        - GST amount
                        - Items purchased
                        - Payment method
                        - Potential tax deduction category (business/medical/education/charity/none)
                        Format as JSON for Australian tax purposes."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }],
            max_tokens=500
        )
        
        receipt_data = json.loads(response.choices[0].message.content)
        
        # Auto-categorize for tax
        receipt_data['tax_deductible'] = receipt_data.get('category') != 'none'
        receipt_data['fy_year'] = self.get_financial_year(receipt_data['date'])
        
        return receipt_data
    
    def get_financial_year(self, date_str: str) -> str:
        """Get Australian financial year from date"""
        date = datetime.strptime(date_str, "%Y-%m-%d")
        if date.month >= 7:
            return f"FY{date.year + 1}"
        return f"FY{date.year}"
