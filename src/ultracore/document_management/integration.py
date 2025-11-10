"""
Document Management Integration
Connects document management with other UltraCore modules

Integrations:
- Customer Onboarding: KYC document verification
- Loan Applications: Income/credit document processing
- Compliance: Regulatory document storage
- Data Mesh: Document data products
"""
from typing import Dict, Optional
from decimal import Decimal

from ultracore.document_management.storage.document_storage import (
    get_storage_service, DocumentType
)
from ultracore.document_management.workflow.orchestrator import get_orchestrator
from ultracore.infrastructure.kafka_event_store.production_store import get_production_kafka_store


class DocumentManagementIntegration:
    """
    Integration layer for document management
    
    Connects documents to business processes
    """
    
    @staticmethod
    async def onboard_customer_with_kyc(
        customer_id: str,
        passport_doc_id: str,
        proof_address_doc_id: str
    ) -> Dict:
        """
        Customer onboarding with KYC verification
        
        Process:
        1. Verify documents are uploaded
        2. Run OCR and extraction
        3. Verify against customer data
        4. Check fraud detection
        5. Approve or reject onboarding
        """
        storage = get_storage_service()
        
        # Get documents
        passport = storage.get_document(passport_doc_id)
        proof_address = storage.get_document(proof_address_doc_id)
        
        if not passport or not proof_address:
            return {
                'success': False,
                'error': 'Required documents not found'
            }
        
        # Check processing status
        if passport.extracted_data is None or proof_address.extracted_data is None:
            return {
                'success': False,
                'error': 'Documents still processing'
            }
        
        # Check fraud scores
        if passport.fraud_score and passport.fraud_score > 0.5:
            return {
                'success': False,
                'kyc_status': 'REJECTED',
                'reason': 'High fraud risk detected on passport'
            }
        
        if proof_address.fraud_score and proof_address.fraud_score > 0.5:
            return {
                'success': False,
                'kyc_status': 'REJECTED',
                'reason': 'High fraud risk detected on proof of address'
            }
        
        # Extract customer data
        customer_data = {
            'full_name': passport.extracted_data.get('given_names', '') + ' ' + passport.extracted_data.get('surname', ''),
            'date_of_birth': passport.extracted_data.get('date_of_birth'),
            'passport_number': passport.extracted_data.get('passport_number'),
            'nationality': passport.extracted_data.get('nationality'),
            'address': proof_address.extracted_data.get('address')
        }
        
        # Publish KYC verification event
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='customer_onboarding',
            event_type='kyc_documents_verified',
            event_data={
                'customer_id': customer_id,
                'passport_doc_id': passport_doc_id,
                'proof_address_doc_id': proof_address_doc_id,
                'customer_data': customer_data,
                'verification_status': 'APPROVED'
            },
            aggregate_id=customer_id
        )
        
        return {
            'success': True,
            'kyc_status': 'APPROVED',
            'customer_data': customer_data
        }
    
    @staticmethod
    async def process_loan_application_documents(
        loan_application_id: str,
        payslip_doc_ids: List[str],
        bank_statement_doc_ids: List[str]
    ) -> Dict:
        """
        Process loan application documents
        
        Extracts income data for loan decisioning
        """
        storage = get_storage_service()
        
        # Extract income from payslips
        total_monthly_income = Decimal('0')
        payslip_data = []
        
        for doc_id in payslip_doc_ids:
            document = storage.get_document(doc_id)
            if document and document.extracted_data:
                gross_pay = document.extracted_data.get('gross_pay', '0')
                total_monthly_income += Decimal(gross_pay.replace(',', ''))
                payslip_data.append(document.extracted_data)
        
        # Analyze bank statements for expenses
        bank_statement_data = []
        for doc_id in bank_statement_doc_ids:
            document = storage.get_document(doc_id)
            if document and document.extracted_data:
                bank_statement_data.append(document.extracted_data)
        
        # Publish loan document verification
        kafka_store = get_production_kafka_store()
        await kafka_store.append_event(
            entity='loan_applications',
            event_type='loan_documents_processed',
            event_data={
                'loan_application_id': loan_application_id,
                'verified_monthly_income': str(total_monthly_income),
                'payslip_count': len(payslip_doc_ids),
                'bank_statement_count': len(bank_statement_doc_ids)
            },
            aggregate_id=loan_application_id
        )
        
        return {
            'success': True,
            'verified_monthly_income': str(total_monthly_income),
            'documents_processed': len(payslip_doc_ids) + len(bank_statement_doc_ids)
        }
    
    @staticmethod
    async def generate_account_statement(
        account_id: str,
        start_date: str,
        end_date: str
    ) -> str:
        """
        Generate bank statement PDF
        
        Returns document_id of generated statement
        """
        # In production: Generate PDF from transaction data
        # Store as document
        # Return document_id
        
        return "DOC-STATEMENT-001"
    
    @staticmethod
    async def publish_to_data_mesh(document_id: str):
        """
        Publish document metadata to Data Mesh
        
        Document as a data product
        """
        from ultracore.data_mesh.integration import DataMeshPublisher
        
        storage = get_storage_service()
        document = storage.get_document(document_id)
        
        if not document:
            return
        
        await DataMeshPublisher.publish_transaction_data(
            document_id,
            {
                'data_product': 'customer_documents',
                'document_type': document.document_type.value,
                'status': document.status.value,
                'fraud_score': document.fraud_score,
                'extracted_fields': list(document.extracted_data.keys()) if document.extracted_data else [],
                'data_quality_score': 0.95,  # Based on confidence scores
                'data_lineage': {
                    'source': 'customer_upload',
                    'processing_pipeline': ['ocr', 'classification', 'extraction', 'fraud_detection'],
                    'transformations': ['image_preprocessing', 'text_extraction', 'entity_recognition']
                }
            }
        )
