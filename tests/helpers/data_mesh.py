"""
Data Mesh helpers for testing.

Provides schema validation, data quality checks, and federated queries.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal
import json


class DataProductSchema:
    """
    Data product schema definition.
    
    Defines structure, types, and constraints for data products.
    """
    
    def __init__(self, name: str, version: str, schema: Dict[str, Any]):
        self.name = name
        self.version = version
        self.schema = schema
        self.created_at = datetime.utcnow()
    
    def validate(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate data against schema.
        
        Returns:
            (is_valid, errors)
        """
        errors = []
        
        # Check required fields
        required_fields = self.schema.get("required", [])
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Check field types
        properties = self.schema.get("properties", {})
        for field, field_schema in properties.items():
            if field in data:
                expected_type = field_schema.get("type")
                actual_value = data[field]
                
                if not self._check_type(actual_value, expected_type):
                    errors.append(
                        f"Field {field} has wrong type: expected {expected_type}, "
                        f"got {type(actual_value).__name__}"
                    )
        
        return len(errors) == 0, errors
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type."""
        type_mapping = {
            "string": str,
            "number": (int, float, Decimal),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type is None:
            return True  # Unknown type, skip validation
        
        return isinstance(value, expected_python_type)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "schema": self.schema,
            "created_at": self.created_at.isoformat()
        }


class DataQualityChecker:
    """
    Data quality checker for data products.
    
    Checks completeness, freshness, accuracy, and consistency.
    """
    
    def __init__(self):
        self.checks_performed = 0
    
    def check_completeness(
        self,
        data: List[Dict[str, Any]],
        required_fields: List[str],
        threshold: float = 0.95
    ) -> Dict[str, Any]:
        """
        Check data completeness.
        
        Args:
            data: Data records
            required_fields: Fields that must be present
            threshold: Minimum completeness threshold (0-1)
        
        Returns:
            Completeness report
        """
        self.checks_performed += 1
        
        if not data:
            return {
                "passed": False,
                "completeness": 0.0,
                "threshold": threshold,
                "missing_fields": required_fields
            }
        
        field_completeness = {}
        
        for field in required_fields:
            complete_count = sum(
                1 for record in data
                if field in record and record[field] is not None
            )
            completeness = complete_count / len(data)
            field_completeness[field] = completeness
        
        avg_completeness = sum(field_completeness.values()) / len(field_completeness)
        passed = avg_completeness >= threshold
        
        return {
            "passed": passed,
            "completeness": avg_completeness,
            "threshold": threshold,
            "field_completeness": field_completeness,
            "records_checked": len(data)
        }
    
    def check_freshness(
        self,
        data: List[Dict[str, Any]],
        timestamp_field: str = "created_at",
        max_age_hours: int = 1
    ) -> Dict[str, Any]:
        """
        Check data freshness.
        
        Args:
            data: Data records
            timestamp_field: Field containing timestamp
            max_age_hours: Maximum age in hours
        
        Returns:
            Freshness report
        """
        self.checks_performed += 1
        
        if not data:
            return {
                "passed": False,
                "freshness": "no_data",
                "max_age_hours": max_age_hours
            }
        
        now = datetime.utcnow()
        max_age = timedelta(hours=max_age_hours)
        
        fresh_count = 0
        oldest_record = None
        
        for record in data:
            if timestamp_field not in record:
                continue
            
            timestamp = record[timestamp_field]
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            age = now - timestamp
            
            if age <= max_age:
                fresh_count += 1
            
            if oldest_record is None or age > (now - oldest_record):
                oldest_record = timestamp
        
        freshness_pct = fresh_count / len(data)
        passed = freshness_pct >= 0.95
        
        return {
            "passed": passed,
            "freshness_pct": freshness_pct,
            "max_age_hours": max_age_hours,
            "oldest_record_age_hours": (
                (now - oldest_record).total_seconds() / 3600
                if oldest_record else None
            ),
            "records_checked": len(data)
        }
    
    def check_consistency(
        self,
        data: List[Dict[str, Any]],
        consistency_rules: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Check data consistency.
        
        Args:
            data: Data records
            consistency_rules: List of consistency rules
        
        Returns:
            Consistency report
        """
        self.checks_performed += 1
        
        violations = []
        
        for rule in consistency_rules:
            rule_type = rule.get("type")
            
            if rule_type == "unique":
                field = rule["field"]
                values = [r.get(field) for r in data if field in r]
                if len(values) != len(set(values)):
                    violations.append(f"Duplicate values in {field}")
            
            elif rule_type == "range":
                field = rule["field"]
                min_val = rule.get("min")
                max_val = rule.get("max")
                
                for record in data:
                    if field in record:
                        value = record[field]
                        if min_val is not None and value < min_val:
                            violations.append(
                                f"{field} value {value} below minimum {min_val}"
                            )
                        if max_val is not None and value > max_val:
                            violations.append(
                                f"{field} value {value} above maximum {max_val}"
                            )
        
        passed = len(violations) == 0
        
        return {
            "passed": passed,
            "violations": violations,
            "rules_checked": len(consistency_rules),
            "records_checked": len(data)
        }


class FederatedQueryEngine:
    """
    Federated query engine for data mesh.
    
    Queries across multiple data products.
    """
    
    def __init__(self):
        self.data_products = {}
        self.queries_executed = 0
    
    def register_data_product(
        self,
        name: str,
        data_source: Any
    ):
        """Register a data product."""
        self.data_products[name] = data_source
    
    def query(
        self,
        data_product: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query a data product.
        
        Args:
            data_product: Data product name
            filters: Filter conditions
            limit: Maximum number of results
        
        Returns:
            Query results
        """
        self.queries_executed += 1
        
        if data_product not in self.data_products:
            raise ValueError(f"Data product not found: {data_product}")
        
        data_source = self.data_products[data_product]
        
        # Apply filters
        results = data_source
        if filters:
            results = [
                record for record in results
                if all(
                    record.get(k) == v
                    for k, v in filters.items()
                )
            ]
        
        # Apply limit
        if limit:
            results = results[:limit]
        
        return results
    
    def join(
        self,
        left_product: str,
        right_product: str,
        left_key: str,
        right_key: str
    ) -> List[Dict[str, Any]]:
        """
        Join two data products.
        
        Args:
            left_product: Left data product
            right_product: Right data product
            left_key: Join key in left product
            right_key: Join key in right product
        
        Returns:
            Joined results
        """
        self.queries_executed += 1
        
        left_data = self.data_products.get(left_product, [])
        right_data = self.data_products.get(right_product, [])
        
        # Build index on right data
        right_index = {}
        for record in right_data:
            key_value = record.get(right_key)
            if key_value:
                right_index[key_value] = record
        
        # Join
        results = []
        for left_record in left_data:
            left_key_value = left_record.get(left_key)
            if left_key_value and left_key_value in right_index:
                joined = {**left_record, **right_index[left_key_value]}
                results.append(joined)
        
        return results
    
    def aggregate(
        self,
        data_product: str,
        group_by: str,
        aggregations: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Aggregate data product.
        
        Args:
            data_product: Data product name
            group_by: Field to group by
            aggregations: Aggregation functions (field -> function)
        
        Returns:
            Aggregated results
        """
        self.queries_executed += 1
        
        data = self.data_products.get(data_product, [])
        
        # Group data
        groups = {}
        for record in data:
            key = record.get(group_by)
            if key not in groups:
                groups[key] = []
            groups[key].append(record)
        
        # Aggregate
        results = []
        for key, group_records in groups.items():
            result = {group_by: key}
            
            for field, func in aggregations.items():
                values = [r.get(field) for r in group_records if field in r]
                
                if func == "count":
                    result[f"{field}_count"] = len(values)
                elif func == "sum":
                    result[f"{field}_sum"] = sum(values)
                elif func == "avg":
                    result[f"{field}_avg"] = sum(values) / len(values) if values else 0
                elif func == "min":
                    result[f"{field}_min"] = min(values) if values else None
                elif func == "max":
                    result[f"{field}_max"] = max(values) if values else None
            
            results.append(result)
        
        return results


class DataLineageTracker:
    """Track data lineage for data products."""
    
    def __init__(self):
        self.lineage = {}
    
    def track(
        self,
        data_product: str,
        source: str,
        transformation: str,
        metadata: Optional[Dict] = None
    ):
        """Track data lineage."""
        if data_product not in self.lineage:
            self.lineage[data_product] = []
        
        self.lineage[data_product].append({
            "source": source,
            "transformation": transformation,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_lineage(self, data_product: str) -> List[Dict[str, Any]]:
        """Get lineage for data product."""
        return self.lineage.get(data_product, [])
    
    def get_upstream_sources(self, data_product: str) -> List[str]:
        """Get upstream sources for data product."""
        lineage = self.get_lineage(data_product)
        return list(set(item["source"] for item in lineage))
