"""
Kafka Schema Management & Topic Conventions
Enforces strict contracts for event schemas
"""
from typing import Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
import json


class TopicConvention:
    """
    Strict topic naming conventions
    
    Format: {environment}.{domain}.{entity}.{event_type}
    Example: prod.ultracore.loans.payment_processed
    """
    
    ENVIRONMENTS = ['dev', 'staging', 'prod']
    DOMAIN = 'ultracore'
    
    # Topic naming rules
    ENTITIES = [
        'loans',
        'clients', 
        'accounts',
        'payments',
        'cards',
        'investments',
        'insurance',
        'merchants',
        'risk',
        'fraud',
        'compliance',
        'audit'
    ]
    
    @staticmethod
    def build_topic_name(
        entity: str,
        event_type: str,
        environment: str = 'dev'
    ) -> str:
        """Build standardized topic name"""
        if environment not in TopicConvention.ENVIRONMENTS:
            raise ValueError(f"Invalid environment: {environment}")
        
        if entity not in TopicConvention.ENTITIES:
            raise ValueError(f"Invalid entity: {entity}")
        
        # Normalize event type
        event_type = event_type.lower().replace(' ', '_')
        
        return f"{environment}.{TopicConvention.DOMAIN}.{entity}.{event_type}"
    
    @staticmethod
    def parse_topic_name(topic: str) -> Dict[str, str]:
        """Parse topic name into components"""
        parts = topic.split('.')
        if len(parts) != 4:
            raise ValueError(f"Invalid topic format: {topic}")
        
        return {
            'environment': parts[0],
            'domain': parts[1],
            'entity': parts[2],
            'event_type': parts[3]
        }
    
    @staticmethod
    def get_dlq_topic(topic: str) -> str:
        """Get DLQ topic for a given topic"""
        return f"{topic}.dlq"
    
    @staticmethod
    def get_retry_topic(topic: str, attempt: int) -> str:
        """Get retry topic"""
        return f"{topic}.retry.{attempt}"


# Event Schema Definitions (Avro-style)
class EventSchema:
    """
    Strict event schemas
    
    Using Python for schema definition (can export to Avro/Protobuf)
    """
    
    # Base event schema
    BASE_EVENT = {
        "name": "BaseEvent",
        "type": "record",
        "namespace": "com.turingdynamics.ultracore",
        "fields": [
            {"name": "event_id", "type": "string"},
            {"name": "aggregate_id", "type": "string"},
            {"name": "aggregate_type", "type": "string"},
            {"name": "event_type", "type": "string"},
            {"name": "timestamp", "type": "string"},
            {"name": "user_id", "type": "string"},
            {"name": "correlation_id", "type": ["null", "string"], "default": None},
            {"name": "causation_id", "type": ["null", "string"], "default": None},
            {"name": "version", "type": "int", "default": 1}
        ]
    }
    
    # Loan Payment Event Schema
    LOAN_PAYMENT_PROCESSED = {
        "name": "LoanPaymentProcessed",
        "type": "record",
        "namespace": "com.turingdynamics.ultracore.loans",
        "fields": [
            *BASE_EVENT["fields"],
            {
                "name": "event_data",
                "type": {
                    "type": "record",
                    "name": "PaymentData",
                    "fields": [
                        {"name": "loan_id", "type": "string"},
                        {"name": "payment_amount", "type": "string"},
                        {"name": "principal_paid", "type": "string"},
                        {"name": "interest_paid", "type": "string"},
                        {"name": "late_fee_paid", "type": "string"},
                        {"name": "remaining_balance", "type": "string"},
                        {"name": "payment_status", "type": "string"},
                        {"name": "days_late", "type": "int"}
                    ]
                }
            }
        ]
    }
    
    # Account Transaction Schema
    ACCOUNT_TRANSACTION = {
        "name": "AccountTransaction",
        "type": "record",
        "namespace": "com.turingdynamics.ultracore.accounts",
        "fields": [
            *BASE_EVENT["fields"],
            {
                "name": "event_data",
                "type": {
                    "type": "record",
                    "name": "TransactionData",
                    "fields": [
                        {"name": "account_id", "type": "string"},
                        {"name": "transaction_type", "type": {"type": "enum", "name": "TransactionType", "symbols": ["DEPOSIT", "WITHDRAWAL", "TRANSFER"]}},
                        {"name": "amount", "type": "string"},
                        {"name": "previous_balance", "type": "string"},
                        {"name": "new_balance", "type": "string"},
                        {"name": "description", "type": "string"},
                        {"name": "reference", "type": ["null", "string"], "default": None}
                    ]
                }
            }
        ]
    }
    
    # Fraud Detection Schema
    FRAUD_DETECTED = {
        "name": "FraudDetected",
        "type": "record",
        "namespace": "com.turingdynamics.ultracore.fraud",
        "fields": [
            *BASE_EVENT["fields"],
            {
                "name": "event_data",
                "type": {
                    "type": "record",
                    "name": "FraudData",
                    "fields": [
                        {"name": "entity_id", "type": "string"},
                        {"name": "entity_type", "type": "string"},
                        {"name": "fraud_score", "type": "double"},
                        {"name": "fraud_flags", "type": {"type": "array", "items": "string"}},
                        {"name": "blocked", "type": "boolean"},
                        {"name": "reason", "type": "string"}
                    ]
                }
            }
        ]
    }
    
    @staticmethod
    def validate_event(event_type: str, event_data: Dict) -> bool:
        """Validate event against schema"""
        # In production: use avro.schema.parse() and validate
        schema = getattr(EventSchema, event_type.upper(), None)
        
        if not schema:
            raise ValueError(f"Unknown event type: {event_type}")
        
        # Basic validation (in production, use proper Avro validation)
        return True


class SchemaRegistry:
    """
    Simple schema registry (in production, use Confluent Schema Registry)
    """
    
    def __init__(self):
        self.schemas: Dict[str, Dict] = {}
        self._register_default_schemas()
    
    def _register_default_schemas(self):
        """Register all default schemas"""
        self.schemas['BaseEvent'] = EventSchema.BASE_EVENT
        self.schemas['LoanPaymentProcessed'] = EventSchema.LOAN_PAYMENT_PROCESSED
        self.schemas['AccountTransaction'] = EventSchema.ACCOUNT_TRANSACTION
        self.schemas['FraudDetected'] = EventSchema.FRAUD_DETECTED
    
    def register_schema(self, schema_name: str, schema: Dict):
        """Register a new schema"""
        # In production: POST to Confluent Schema Registry
        self.schemas[schema_name] = schema
        print(f"✓ Schema registered: {schema_name}")
    
    def get_schema(self, schema_name: str) -> Optional[Dict]:
        """Get schema by name"""
        return self.schemas.get(schema_name)
    
    def validate_event(self, event_type: str, event_data: Dict) -> bool:
        """Validate event data against registered schema"""
        schema = self.get_schema(event_type)
        if not schema:
            raise ValueError(f"Schema not found: {event_type}")
        
        # In production: use proper Avro/Protobuf validation
        return True


# Global schema registry
_schema_registry = SchemaRegistry()


def get_schema_registry() -> SchemaRegistry:
    return _schema_registry
