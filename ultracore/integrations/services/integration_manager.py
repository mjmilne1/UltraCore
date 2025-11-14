"""Integration Manager"""
from typing import List, Dict, Optional
from datetime import datetime
from ..connectors.xero_au_connector import XeroAUConnector
from ..connectors.mytax_ato_connector import MyTaxATOConnector
from ..events import IntegrationProvider, IntegrationType

class IntegrationManager:
    """Manage all third-party integrations"""
    
    def __init__(self):
        """Initialize integration manager"""
        self.connectors = {}
    
    def register_integration(self, integration_id: str,
                            provider: IntegrationProvider,
                            configuration: Dict) -> bool:
        """Register a new integration"""
        if provider == IntegrationProvider.XERO_AU:
            connector = XeroAUConnector(
                client_id=configuration["client_id"],
                client_secret=configuration["client_secret"],
                tenant_id=configuration["tenant_id"]
            )
            self.connectors[integration_id] = connector
            return True
        
        elif provider == IntegrationProvider.MYTAX_ATO:
            connector = MyTaxATOConnector(
                tfn=configuration["tfn"],
                api_key=configuration["api_key"]
            )
            self.connectors[integration_id] = connector
            return True
        
        # Add more providers here
        
        return False
    
    async def sync_integration(self, integration_id: str,
                              sync_type: str,
                              data: Dict) -> Dict:
        """Sync data with integration"""
        connector = self.connectors.get(integration_id)
        if not connector:
            return {
                "success": False,
                "error": "Integration not found"
            }
        
        # Authenticate if needed
        if hasattr(connector, 'authenticate'):
            await connector.authenticate()
        
        # Route to appropriate sync method
        if isinstance(connector, XeroAUConnector):
            if sync_type == "transactions":
                return await connector.export_transactions(
                    data["transactions"],
                    data["date_range_start"],
                    data["date_range_end"]
                )
            elif sync_type == "fees":
                return await connector.export_fees(data["fees"])
        
        elif isinstance(connector, MyTaxATOConnector):
            if sync_type == "capital_gains":
                return await connector.export_capital_gains(
                    data["capital_gains"],
                    data["tax_year"]
                )
            elif sync_type == "dividends":
                return await connector.export_dividend_income(
                    data["dividends"],
                    data["tax_year"]
                )
        
        return {
            "success": False,
            "error": "Unsupported sync type"
        }
    
    def get_integration_status(self, integration_id: str) -> Dict:
        """Get integration status"""
        connector = self.connectors.get(integration_id)
        if not connector:
            return {
                "status": "not_found"
            }
        
        return {
            "status": "active",
            "connector_type": type(connector).__name__,
            "last_sync": None  # Track in database
        }
