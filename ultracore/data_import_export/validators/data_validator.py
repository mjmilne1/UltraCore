"""Data Validation Engine"""
from typing import List, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime

class DataValidator:
    """Comprehensive data validation"""
    
    def validate_import_data(self, rows: List[Dict[str, Any]], 
                            data_type: str) -> Tuple[bool, List[Dict], List[Dict]]:
        """Validate imported data
        Returns: (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        for idx, row in enumerate(rows):
            # Required fields validation
            if not row.get("date"):
                errors.append({"row": idx, "field": "date", "error": "Missing date"})
            
            if not row.get("symbol"):
                errors.append({"row": idx, "field": "symbol", "error": "Missing symbol"})
            
            # Data type validation
            if row.get("quantity"):
                if not isinstance(row["quantity"], (Decimal, int, float)):
                    errors.append({"row": idx, "field": "quantity", "error": "Invalid quantity type"})
                elif row["quantity"] < 0:
                    warnings.append({"row": idx, "field": "quantity", "warning": "Negative quantity"})
            
            if row.get("price"):
                if not isinstance(row["price"], (Decimal, int, float)):
                    errors.append({"row": idx, "field": "price", "error": "Invalid price type"})
                elif row["price"] <= 0:
                    errors.append({"row": idx, "field": "price", "error": "Price must be positive"})
            
            # Business logic validation
            if row.get("amount"):
                expected_amount = row.get("quantity", 0) * row.get("price", 0)
                if abs(row["amount"] - expected_amount) > Decimal("0.01"):
                    warnings.append({
                        "row": idx,
                        "field": "amount",
                        "warning": f"Amount mismatch: expected {expected_amount}, got {row['amount']}"
                    })
        
        is_valid = len(errors) == 0
        return is_valid, errors, warnings
    
    def validate_schema(self, row: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """Validate row against schema"""
        missing_fields = []
        for field in required_fields:
            if field not in row or row[field] is None:
                missing_fields.append(field)
        return missing_fields
