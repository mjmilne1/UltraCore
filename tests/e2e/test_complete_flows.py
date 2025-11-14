"""
End-to-end tests for complete business flows.

Tests complete workflows across all three frameworks.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from ultracore.data_mesh import DataProductRegistry
from ultracore.data_mesh.products import Customer360, AccountBalances
from ultracore.event_sourcing import Event, EventMetadata, EventType
from ultracore.event_sourcing.store.event_store import KafkaEventStore
from ultracore.event_sourcing.handlers import CustomerEventHandler, AccountEventHandler
from ultracore.event_sourcing.projections import (
    ProjectionManager,
    CustomerReadModel,
    AccountReadModel,
)
from ultracore.agentic_ai import AgentOrchestrator
from ultracore.agentic_ai.agents.customer_agent import CustomerAgent


class TestCustomerOnboardingFlow:
    """Test complete customer onboarding flow."""
    
    @pytest.mark.asyncio
    async def test_complete_onboarding(self):
        """Test end-to-end customer onboarding."""
        # Setup
        event_store = KafkaEventStore()
        projection_manager = ProjectionManager(event_store)
        customer_projection = CustomerReadModel()
        projection_manager.register_projection(customer_projection)
        
        orchestrator = AgentOrchestrator()
        customer_agent = CustomerAgent()
        orchestrator.register_agent(customer_agent)
        
        customer_id = "CUST_E2E_001"
        
        # Step 1: Agent initiates onboarding
        onboarding_task = {
            "task_id": "onboard_001",
            "customer_id": customer_id,
            "customer_data": {
                "name": "Jane Smith",
                "email": "jane@example.com",
            },
            "needs": ["onboarding"],
        }
        
        agent_result = await orchestrator.execute_task(
            onboarding_task,
            agent_id="customer_agent"
        )
        
        assert agent_result is not None
        
        # Step 2: Publish customer created event
        event = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.CUSTOMER_CREATED,
                aggregate_id=customer_id,
                aggregate_type="Customer",
                version=1,
                timestamp=datetime.utcnow(),
            ),
            data={
                "name": "Jane Smith",
                "email": "jane@example.com",
            }
        )
        
        await event_store.append_event(event)
        
        # Step 3: Project event to read model
        await projection_manager.project_event(event)
        
        # Step 4: Verify customer in read model
        customer = customer_projection.get_customer(customer_id)
        
        assert customer is not None
        assert customer["name"] == "Jane Smith"
        
        # Step 5: Query customer from Data Mesh
        data_product = Customer360()
        customer_data = await data_product.query(
            filters={"customer_id": customer_id}
        )
        
        assert customer_data is not None


class TestAccountOpeningFlow:
    """Test complete account opening flow."""
    
    @pytest.mark.asyncio
    async def test_complete_account_opening(self):
        """Test end-to-end account opening."""
        # Setup
        event_store = KafkaEventStore()
        projection_manager = ProjectionManager(event_store)
        account_projection = AccountReadModel()
        projection_manager.register_projection(account_projection)
        
        customer_id = "CUST001"
        account_id = "ACC_E2E_001"
        
        # Step 1: Publish account opened event
        event = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.ACCOUNT_OPENED,
                aggregate_id=account_id,
                aggregate_type="Account",
                version=1,
                timestamp=datetime.utcnow(),
            ),
            data={
                "customer_id": customer_id,
                "account_type": "savings",
                "initial_balance": 1000,
                "currency": "AUD",
            }
        )
        
        await event_store.append_event(event)
        
        # Step 2: Project event
        await projection_manager.project_event(event)
        
        # Step 3: Verify account in read model
        account = account_projection.get_account(account_id)
        
        assert account is not None
        assert account["balance"] == 1000
        assert account["status"] == "active"
        
        # Step 4: Query account from Data Mesh
        data_product = AccountBalances()
        account_data = await data_product.query(
            filters={"account_id": account_id}
        )
        
        assert account_data is not None


class TestTransactionFlow:
    """Test complete transaction flow."""
    
    @pytest.mark.asyncio
    async def test_complete_transaction(self):
        """Test end-to-end transaction processing."""
        # Setup
        event_store = KafkaEventStore()
        account_id = "ACC001"
        transaction_id = "TXN_E2E_001"
        
        # Step 1: Create transaction
        create_event = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.TRANSACTION_CREATED,
                aggregate_id=transaction_id,
                aggregate_type="Transaction",
                version=1,
                timestamp=datetime.utcnow(),
            ),
            data={
                "account_id": account_id,
                "amount": 100,
                "currency": "AUD",
                "type": "debit",
            }
        )
        
        await event_store.append_event(create_event)
        
        # Step 2: Post transaction
        post_event = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.TRANSACTION_POSTED,
                aggregate_id=transaction_id,
                aggregate_type="Transaction",
                version=2,
                timestamp=datetime.utcnow(),
                causation_id=create_event.metadata.event_id,
            ),
            data={}
        )
        
        await event_store.append_event(post_event)
        
        # Step 3: Settle transaction
        settle_event = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.TRANSACTION_SETTLED,
                aggregate_id=transaction_id,
                aggregate_type="Transaction",
                version=3,
                timestamp=datetime.utcnow(),
                causation_id=post_event.metadata.event_id,
            ),
            data={}
        )
        
        await event_store.append_event(settle_event)
        
        # Step 4: Verify transaction history
        events = await event_store.get_events(transaction_id)
        
        assert len(events) == 3
        assert events[0].metadata.event_type == EventType.TRANSACTION_CREATED
        assert events[1].metadata.event_type == EventType.TRANSACTION_POSTED
        assert events[2].metadata.event_type == EventType.TRANSACTION_SETTLED


class TestPaymentFlow:
    """Test complete payment flow."""
    
    @pytest.mark.asyncio
    async def test_complete_payment(self):
        """Test end-to-end payment processing."""
        event_store = KafkaEventStore()
        payment_id = "PAY_E2E_001"
        
        # Step 1: Initiate payment
        initiate_event = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.PAYMENT_INITIATED,
                aggregate_id=payment_id,
                aggregate_type="Payment",
                version=1,
                timestamp=datetime.utcnow(),
            ),
            data={
                "from_account": "ACC001",
                "to_account": "ACC002",
                "amount": 500,
                "currency": "AUD",
            }
        )
        
        await event_store.append_event(initiate_event)
        
        # Step 2: Authorize payment
        authorize_event = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.PAYMENT_AUTHORIZED,
                aggregate_id=payment_id,
                aggregate_type="Payment",
                version=2,
                timestamp=datetime.utcnow(),
            ),
            data={}
        )
        
        await event_store.append_event(authorize_event)
        
        # Step 3: Complete payment
        complete_event = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.PAYMENT_COMPLETED,
                aggregate_id=payment_id,
                aggregate_type="Payment",
                version=3,
                timestamp=datetime.utcnow(),
            ),
            data={}
        )
        
        await event_store.append_event(complete_event)
        
        # Verify payment history
        events = await event_store.get_events(payment_id)
        
        assert len(events) == 3
        assert events[-1].metadata.event_type == EventType.PAYMENT_COMPLETED


class TestLoanApplicationFlow:
    """Test complete loan application flow."""
    
    @pytest.mark.asyncio
    async def test_complete_loan_application(self):
        """Test end-to-end loan application."""
        event_store = KafkaEventStore()
        loan_id = "LOAN_E2E_001"
        
        # Step 1: Submit application
        submit_event = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.LOAN_APPLICATION_SUBMITTED,
                aggregate_id=loan_id,
                aggregate_type="Loan",
                version=1,
                timestamp=datetime.utcnow(),
            ),
            data={
                "customer_id": "CUST001",
                "amount": 50000,
                "term_months": 60,
                "purpose": "home_improvement",
            }
        )
        
        await event_store.append_event(submit_event)
        
        # Step 2: Approve loan
        approve_event = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.LOAN_APPROVED,
                aggregate_id=loan_id,
                aggregate_type="Loan",
                version=2,
                timestamp=datetime.utcnow(),
            ),
            data={
                "interest_rate": 0.05,
                "approved_amount": 50000,
            }
        )
        
        await event_store.append_event(approve_event)
        
        # Step 3: Disburse loan
        disburse_event = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.LOAN_DISBURSED,
                aggregate_id=loan_id,
                aggregate_type="Loan",
                version=3,
                timestamp=datetime.utcnow(),
            ),
            data={
                "disbursement_account": "ACC001",
                "disbursement_date": datetime.utcnow().isoformat(),
            }
        )
        
        await event_store.append_event(disburse_event)
        
        # Verify loan history
        events = await event_store.get_events(loan_id)
        
        assert len(events) == 3
        assert events[0].metadata.event_type == EventType.LOAN_APPLICATION_SUBMITTED
        assert events[1].metadata.event_type == EventType.LOAN_APPROVED
        assert events[2].metadata.event_type == EventType.LOAN_DISBURSED


class TestCrossSystemIntegration:
    """Test integration across all three systems."""
    
    @pytest.mark.asyncio
    async def test_agent_event_datamesh_integration(self):
        """Test Agent → Event Sourcing → Data Mesh flow."""
        # Setup all systems
        event_store = KafkaEventStore()
        projection_manager = ProjectionManager(event_store)
        customer_projection = CustomerReadModel()
        projection_manager.register_projection(customer_projection)
        
        orchestrator = AgentOrchestrator()
        customer_agent = CustomerAgent()
        orchestrator.register_agent(customer_agent)
        
        data_registry = DataProductRegistry()
        customer_product = Customer360()
        data_registry.register(customer_product)
        
        customer_id = "CUST_INTEGRATION_001"
        
        # Step 1: Agent processes request
        task = {
            "task_id": "integration_001",
            "customer_id": customer_id,
            "action": "create_customer",
            "customer_data": {
                "name": "Integration Test",
                "email": "integration@test.com",
            }
        }
        
        agent_result = await orchestrator.execute_task(
            task,
            agent_id="customer_agent"
        )
        
        assert agent_result is not None
        
        # Step 2: Publish event
        event = Event(
            metadata=EventMetadata(
                event_id=str(uuid4()),
                event_type=EventType.CUSTOMER_CREATED,
                aggregate_id=customer_id,
                aggregate_type="Customer",
                version=1,
                timestamp=datetime.utcnow(),
            ),
            data=task["customer_data"]
        )
        
        await event_store.append_event(event)
        await projection_manager.project_event(event)
        
        # Step 3: Query from Data Mesh
        customer_data = await customer_product.query(
            filters={"customer_id": customer_id}
        )
        
        # Verify data flows through all systems
        assert agent_result is not None
        assert customer_projection.get_customer(customer_id) is not None
        assert customer_data is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
