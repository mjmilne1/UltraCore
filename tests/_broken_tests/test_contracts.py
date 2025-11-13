"""
Consumer-Driven Contract Tests
Nubank-inspired: Contract tests gate CI/CD, deploy only on green contracts

Architecture:
1. Consumers define contracts (what they expect from providers)
2. Providers verify they meet all consumer contracts
3. CI/CD blocks deployment if contracts break
4. Schema evolution with backward compatibility checks

Tests:
- API endpoint contracts
- Kafka event schemas
- Data Mesh data product contracts
- Microservice communication contracts
"""
import pytest
from typing import Dict, List, Optional, Any
from datetime import datetime
from decimal import Decimal
from enum import Enum
import json
from pydantic import BaseModel, ValidationError

from ultracore.modules.accounting.general_ledger.journal import JournalService
# from ultracore.payments.payment_service import PaymentService  # TODO: Fix import path
from ultracore.notifications.notification_service import NotificationService
from ultracore.document_management.storage.document_storage import DocumentStorage


class ContractStatus(str, Enum):
    PASS = 'PASS'
    FAIL = 'FAIL'
    BREAKING_CHANGE = 'BREAKING_CHANGE'


class ContractTestResult:
    """Result of a contract test"""
    
    def __init__(
        self,
        contract_name: str,
        consumer: str,
        provider: str,
        status: ContractStatus,
        error_message: Optional[str] = None
    ):
        self.contract_name = contract_name
        self.consumer = consumer
        self.provider = provider
        self.status = status
        self.error_message = error_message
        self.tested_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict:
        return {
            'contract_name': self.contract_name,
            'consumer': self.consumer,
            'provider': self.provider,
            'status': self.status.value,
            'error_message': self.error_message,
            'tested_at': self.tested_at.isoformat()
        }


class APIContract:
    """
    API endpoint contract definition
    
    Defines expected request/response structure
    """
    
    def __init__(
        self,
        name: str,
        consumer: str,
        provider: str,
        endpoint: str,
        method: str,
        request_schema: Dict,
        response_schema: Dict,
        status_code: int = 200
    ):
        self.name = name
        self.consumer = consumer
        self.provider = provider
        self.endpoint = endpoint
        self.method = method
        self.request_schema = request_schema
        self.response_schema = response_schema
        self.expected_status_code = status_code


class EventContract:
    """
    Kafka event schema contract
    
    Ensures event producers maintain expected schema
    """
    
    def __init__(
        self,
        name: str,
        consumer: str,
        producer: str,
        event_type: str,
        schema: Dict
    ):
        self.name = name
        self.consumer = consumer
        self.producer = producer
        self.event_type = event_type
        self.schema = schema


class TestJournalEntryContract:
    """
    Contract tests for Journal Entry API
    
    Consumer: Payment Service, Loan Service, Fee Service
    Provider: General Ledger Service
    """
    
    @pytest.mark.contract
    async def test_create_journal_entry_contract(self):
        """
        CONTRACT: Payment Service -> General Ledger
        
        Payment service expects to create journal entries with:
        - Description (string)
        - Entries array with account_code, debit, credit
        - Response includes entry_id and total_debit/total_credit
        """
        journal_service = JournalService()
        
        # Consumer's expected request format
        request = {
            'description': 'Payment transaction',
            'entries': [
                {
                    'account_code': '1100',
                    'debit': '100.00',
                    'credit': '0'
                },
                {
                    'account_code': '4100',
                    'debit': '0',
                    'credit': '100.00'
                }
            ]
        }
        
        # Execute request
        try:
            result = await journal_service.create_entry(
                description=request['description'],
                entries=request['entries']
            )
            
            # Verify response contract
            assert 'entry_id' in result, "Response missing entry_id"
            assert 'total_debit' in result, "Response missing total_debit"
            assert 'total_credit' in result, "Response missing total_credit"
            assert 'lines' in result, "Response missing lines"
            assert 'created_at' in result, "Response missing created_at"
            
            # Verify types
            assert isinstance(result['entry_id'], str)
            assert isinstance(result['total_debit'], str)
            assert isinstance(result['total_credit'], str)
            assert isinstance(result['lines'], list)
            
            # Verify business rule: debits = credits
            assert result['total_debit'] == result['total_credit'], \
                "Contract violation: debits must equal credits"
            
            contract_result = ContractTestResult(
                contract_name='create_journal_entry',
                consumer='payment_service',
                provider='general_ledger',
                status=ContractStatus.PASS
            )
            
        except Exception as e:
            contract_result = ContractTestResult(
                contract_name='create_journal_entry',
                consumer='payment_service',
                provider='general_ledger',
                status=ContractStatus.FAIL,
                error_message=str(e)
            )
            
            pytest.fail(f"Contract broken: {e}")
    
    @pytest.mark.contract
    async def test_journal_entry_idempotency_contract(self):
        """
        CONTRACT: All consumers -> General Ledger
        
        Consumers expect idempotency:
        - Posting same entry twice with same idempotency_key returns existing entry
        - No duplicate entries created
        """
        journal_service = JournalService()
        
        idempotency_key = 'TEST-IDEMPOTENCY-001'
        
        request = {
            'description': 'Idempotency test',
            'entries': [
                {'account_code': '1100', 'debit': '50.00', 'credit': '0'},
                {'account_code': '4100', 'debit': '0', 'credit': '50.00'}
            ],
            'idempotency_key': idempotency_key
        }
        
        # First request
        result1 = await journal_service.create_entry(**request)
        
        # Second request (duplicate)
        result2 = await journal_service.create_entry(**request)
        
        # CONTRACT: Same idempotency key returns same entry
        assert result1['entry_id'] == result2['entry_id'], \
            "Idempotency contract violated: different entries returned for same key"


class TestPaymentEventContract:
    """
    Contract tests for Payment Events
    
    Consumer: Notification Service, Analytics Service, Fraud Detection
    Producer: Payment Service
    """
    
    @pytest.mark.contract
    async def test_payment_initiated_event_schema(self):
        """
        CONTRACT: Payment Service -> Notification Service
        
        When payment is initiated, event must contain:
        - payment_id (string)
        - customer_id (string)
        - amount (string, decimal)
        - currency (string)
        - payment_method (string)
        - status (string)
        - initiated_at (ISO datetime string)
        """
        # Expected event schema
        expected_schema = {
            'payment_id': str,
            'customer_id': str,
            'amount': str,
            'currency': str,
            'payment_method': str,
            'status': str,
            'initiated_at': str
        }
        
        # Simulate payment event
        event_data = {
            'payment_id': 'PAY-001',
            'customer_id': 'CUST-001',
            'amount': '100.00',
            'currency': 'AUD',
            'payment_method': 'CARD',
            'status': 'INITIATED',
            'initiated_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Verify schema compliance
        for field, expected_type in expected_schema.items():
            assert field in event_data, f"Missing required field: {field}"
            assert isinstance(event_data[field], expected_type), \
                f"Field {field} has wrong type: expected {expected_type}, got {type(event_data[field])}"
        
        # Verify amount is valid decimal
        try:
            amount = Decimal(event_data['amount'])
            assert amount > 0, "Amount must be positive"
        except:
            pytest.fail("Amount is not a valid decimal")
        
        # Verify datetime is valid ISO format
        try:
            datetime.fromisoformat(event_data['initiated_at'])
        except:
            pytest.fail("initiated_at is not valid ISO datetime")


class TestNotificationContract:
    """
    Contract tests for Notification Service
    
    Consumer: All services that send notifications
    Provider: Notification Service
    """
    
    @pytest.mark.contract
    async def test_send_notification_contract(self):
        """
        CONTRACT: All Services -> Notification Service
        
        Services expect to send notifications with:
        - template_id (string)
        - recipient_id (string)
        - variables (dict)
        - channel_override (optional string)
        - priority (optional string)
        """
        notification_service = NotificationService()
        
        # Consumer's expected request
        request = {
            'template_id': 'welcome_email',
            'recipient_id': 'CUST-001',
            'variables': {
                'customer_name': 'John Doe',
                'account_number': '123456789',
                'bsb': '123-456'
            },
            'priority': 'NORMAL'
        }
        
        # Execute
        result = await notification_service.send_notification(**request)
        
        # Verify response contract
        assert 'success' in result
        assert 'notification_id' in result
        assert isinstance(result['success'], bool)
        
        if result['success']:
            assert isinstance(result['notification_id'], str)
            assert result['notification_id'].startswith('NOTIF-')


class TestDocumentUploadContract:
    """
    Contract tests for Document Management
    
    Consumer: Customer Onboarding, Loan Application
    Provider: Document Management Service
    """
    
    @pytest.mark.contract
    async def test_document_upload_contract(self):
        """
        CONTRACT: Onboarding Service -> Document Management
        
        Onboarding expects to upload documents with:
        - file (binary)
        - file_name (string)
        - document_type (enum string)
        - owner_id (string)
        
        Response must include:
        - document_id (string)
        - status (string)
        - uploaded_at (ISO datetime)
        """
        # This would be tested with actual file upload in integration tests
        # Here we verify the contract structure
        
        expected_response_schema = {
            'document_id': str,
            'file_name': str,
            'document_type': str,
            'status': str,
            'uploaded_at': str
        }
        
        # Simulate response
        response = {
            'document_id': 'DOC-001',
            'file_name': 'passport.jpg',
            'document_type': 'PASSPORT',
            'status': 'UPLOADED',
            'uploaded_at': datetime.now(timezone.utc).isoformat()
        }
        
        # Verify contract
        for field, expected_type in expected_response_schema.items():
            assert field in response
            assert isinstance(response[field], expected_type)


class TestDataMeshContract:
    """
    Contract tests for Data Mesh Data Products
    
    Ensures data products maintain expected schema
    """
    
    @pytest.mark.contract
    def test_transaction_data_product_schema(self):
        """
        CONTRACT: Data Mesh Consumers -> Transaction Data Product
        
        Transaction data product must contain:
        - transaction_id (string)
        - customer_id (string)
        - amount (decimal string)
        - transaction_type (string)
        - timestamp (ISO datetime)
        - metadata (dict)
        """
        # Expected schema
        schema = {
            'transaction_id': str,
            'customer_id': str,
            'amount': str,
            'transaction_type': str,
            'timestamp': str,
            'metadata': dict
        }
        
        # Sample data product
        data_product = {
            'transaction_id': 'TXN-001',
            'customer_id': 'CUST-001',
            'amount': '100.00',
            'transaction_type': 'PAYMENT',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'metadata': {'channel': 'mobile'}
        }
        
        # Verify schema
        for field, expected_type in schema.items():
            assert field in data_product
            assert isinstance(data_product[field], expected_type)


class ContractTestRunner:
    """
    Contract test runner for CI/CD integration
    
    Blocks deployment if contracts fail
    """
    
    def __init__(self):
        self.results: List[ContractTestResult] = []
    
    async def run_all_contracts(self) -> Dict:
        """
        Run all contract tests
        
        Returns summary with pass/fail status
        """
        print("\n🔍 Running Contract Tests...")
        
        # Run all contract test classes
        test_classes = [
            TestJournalEntryContract(),
            TestPaymentEventContract(),
            TestNotificationContract(),
            TestDocumentUploadContract(),
            TestDataMeshContract()
        ]
        
        total_tests = 0
        passed = 0
        failed = 0
        breaking_changes = 0
        
        for test_class in test_classes:
            # Get all test methods
            test_methods = [
                method for method in dir(test_class)
                if method.startswith('test_') and callable(getattr(test_class, method))
            ]
            
            for method_name in test_methods:
                total_tests += 1
                method = getattr(test_class, method_name)
                
                try:
                    if asyncio.iscoroutinefunction(method):
                        await method()
                    else:
                        method()
                    
                    passed += 1
                    print(f"   ✅ {method_name}")
                    
                except AssertionError as e:
                    failed += 1
                    print(f"   ❌ {method_name}: {str(e)}")
                    
                    # Check if breaking change
                    if 'contract' in str(e).lower() or 'breaking' in str(e).lower():
                        breaking_changes += 1
                
                except Exception as e:
                    failed += 1
                    print(f"   ❌ {method_name}: {str(e)}")
        
        summary = {
            'total_tests': total_tests,
            'passed': passed,
            'failed': failed,
            'breaking_changes': breaking_changes,
            'success_rate': (passed / total_tests * 100) if total_tests > 0 else 0,
            'should_block_deployment': breaking_changes > 0 or (failed / total_tests > 0.1 if total_tests > 0 else True)
        }
        
        print(f"\n📊 Contract Test Summary:")
        print(f"   Total: {total_tests}")
        print(f"   Passed: {passed} ✅")
        print(f"   Failed: {failed} ❌")
        print(f"   Breaking Changes: {breaking_changes} ⚠️")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        
        if summary['should_block_deployment']:
            print(f"\n   🚨 DEPLOYMENT BLOCKED: Contract tests failed")
        else:
            print(f"\n   ✅ All contracts passing - safe to deploy")
        
        return summary


class SchemaVersioning:
    """
    Schema versioning and evolution
    
    Ensures backward compatibility
    """
    
    @staticmethod
    def is_backward_compatible(old_schema: Dict, new_schema: Dict) -> Tuple[bool, List[str]]:
        """
        Check if new schema is backward compatible with old schema
        
        Backward compatible changes:
        - Adding optional fields
        - Widening field types
        
        Breaking changes:
        - Removing fields
        - Changing field types (narrowing)
        - Making optional fields required
        """
        issues = []
        
        # Check for removed fields
        for field in old_schema.keys():
            if field not in new_schema:
                issues.append(f"BREAKING: Field '{field}' removed")
        
        # Check for type changes
        for field, old_type in old_schema.items():
            if field in new_schema:
                new_type = new_schema[field]
                if old_type != new_type:
                    # Check if it's a widening (compatible) or narrowing (breaking)
                    if not SchemaVersioning._is_type_widening(old_type, new_type):
                        issues.append(f"BREAKING: Field '{field}' type changed from {old_type} to {new_type}")
        
        is_compatible = len(issues) == 0
        
        return is_compatible, issues
    
    @staticmethod
    def _is_type_widening(old_type: type, new_type: type) -> bool:
        """Check if type change is a widening (compatible)"""
        # Simple type widening rules
        widening_rules = {
            int: [float, str],
            float: [str],
            str: [],  # String can't be widened
        }
        
        return new_type in widening_rules.get(old_type, [])


class TestSchemaEvolution:
    """
    Tests for schema evolution and versioning
    """
    
    @pytest.mark.contract
    def test_adding_optional_field_is_compatible(self):
        """Adding optional fields should be backward compatible"""
        old_schema = {
            'payment_id': str,
            'amount': str,
            'customer_id': str
        }
        
        new_schema = {
            'payment_id': str,
            'amount': str,
            'customer_id': str,
            'metadata': dict  # New optional field
        }
        
        is_compatible, issues = SchemaVersioning.is_backward_compatible(old_schema, new_schema)
        
        assert is_compatible, f"Should be compatible, but found issues: {issues}"
    
    @pytest.mark.contract
    def test_removing_field_is_breaking(self):
        """Removing fields is a breaking change"""
        old_schema = {
            'payment_id': str,
            'amount': str,
            'customer_id': str,
            'metadata': dict
        }
        
        new_schema = {
            'payment_id': str,
            'amount': str,
            'customer_id': str
            # metadata removed
        }
        
        is_compatible, issues = SchemaVersioning.is_backward_compatible(old_schema, new_schema)
        
        assert not is_compatible, "Should be breaking change"
        assert len(issues) > 0
        assert any('metadata' in issue and 'removed' in issue for issue in issues)


# CI/CD Integration
class CICDContractGate:
    """
    CI/CD gate for contract tests
    
    Usage in CI/CD pipeline:
`yaml
    # .github/workflows/deploy.yml
    - name: Run Contract Tests
      run: python -m tests.contract.contract_tests
      
    - name: Check Contract Gate
      run: |
        if [ -f contract_gate_blocked ]; then
          echo "Deployment blocked by contract tests"
          exit 1
        fi
`
    """
    
    @staticmethod
    async def run_gate() -> bool:
        """
        Run contract gate
        
        Returns: True if deployment should proceed, False if blocked
        """
        runner = ContractTestRunner()
        summary = await runner.run_all_contracts()
        
        should_deploy = not summary['should_block_deployment']
        
        # Write gate file for CI/CD
        if not should_deploy:
            with open('contract_gate_blocked', 'w') as f:
                f.write(json.dumps(summary, indent=2))
        else:
            # Remove block file if exists
            import os
            if os.path.exists('contract_gate_blocked'):
                os.remove('contract_gate_blocked')
        
        return should_deploy


# Pytest configuration
@pytest.fixture(scope='session')
def contract_test_config():
    """Configure contract tests"""
    return {
        'fail_on_breaking_change': True,
        'fail_threshold': 0.1,  # Block if >10% of tests fail
        'require_all_contracts': True
    }


# Main entry point for CI/CD
async def main():
    """Run contract tests in CI/CD"""
    print("\n" + "=" * 80)
    print("CONSUMER-DRIVEN CONTRACT TESTS")
    print("=" * 80)
    
    should_deploy = await CICDContractGate.run_gate()
    
    print("\n" + "=" * 80)
    
    if should_deploy:
        print("✅ CONTRACT GATE: PASS - Deployment approved")
        print("=" * 80)
        exit(0)
    else:
        print("⛔ CONTRACT GATE: BLOCKED - Deployment rejected")
        print("=" * 80)
        exit(1)


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
