"""
MCP Tools for Additional Modules
Shares, COB, Configuration Management

Enables AI agents to interact with:
- Share accounts and products
- COB processing
- Configuration management
"""

from typing import List, Dict, Any, Optional
from datetime import date
from decimal import Decimal


class AdditionalModulesMCPTools:
    """
    MCP Tools for Additional Modules
    
    Provides AI agents with tools to:
    - Manage share products and accounts
    - Monitor COB processing
    - Manage configurations and feature flags
    """
    
    def __init__(self, share_service=None, cob_engine=None, config_manager=None):
        self.share_service = share_service
        self.cob_engine = cob_engine
        self.config_manager = config_manager
        
    # ========================================================================
    # SHARE PRODUCT TOOLS
    # ========================================================================
    
    def list_share_products(
        self,
        product_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List available share products
        
        Args:
            product_type: Filter by product type (optional)
            
        Returns:
            List of share products
        """
        if not self.share_service:
            return []
        
        products = self.share_service.list_active_products()
        
        if product_type:
            products = [p for p in products if p.product_type.value == product_type]
        
        return [
            {
                "product_id": p.product_id,
                "product_code": p.product_code,
                "product_name": p.product_name,
                "product_type": p.product_type.value,
                "nominal_price": str(p.nominal_price),
                "dividend_rate": str(p.dividend_rate) if p.dividend_rate else None,
                "minimum_shares": p.minimum_shares
            }
            for p in products
        ]
        
    def get_share_product(
        self,
        product_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get share product details
        
        Args:
            product_id: Product ID
            
        Returns:
            Product details
        """
        if not self.share_service:
            return None
        
        product = self.share_service.get_product(product_id)
        
        if not product:
            return None
        
        return {
            "product_id": product.product_id,
            "product_code": product.product_code,
            "product_name": product.product_name,
            "product_type": product.product_type.value,
            "description": product.description,
            "nominal_price": str(product.nominal_price),
            "minimum_shares": product.minimum_shares,
            "maximum_shares": product.maximum_shares,
            "dividend_rate": str(product.dividend_rate) if product.dividend_rate else None,
            "dividend_frequency": product.dividend_frequency,
            "is_redeemable": product.is_redeemable,
            "has_voting_rights": product.has_voting_rights,
            "total_shares_issued": product.total_shares_issued,
            "total_shares_outstanding": product.total_shares_outstanding
        }
        
    # ========================================================================
    # SHARE ACCOUNT TOOLS
    # ========================================================================
    
    def create_share_account(
        self,
        client_id: str,
        product_id: str,
        num_shares: int,
        price_per_share: float,
        created_by: str = "ai_agent"
    ) -> Dict[str, Any]:
        """
        Create a new share account
        
        Args:
            client_id: Client ID
            product_id: Share product ID
            num_shares: Number of shares to purchase
            price_per_share: Price per share
            created_by: Creator ID
            
        Returns:
            Created account details
        """
        from ..modules.shares.models import CreateShareAccountRequest
        
        if not self.share_service:
            return {"error": "Share service not available"}
        
        request = CreateShareAccountRequest(
            client_id=client_id,
            product_id=product_id,
            num_shares=num_shares,
            price_per_share=Decimal(str(price_per_share)),
            created_by=created_by
        )
        
        account = self.share_service.create_account(request)
        
        return {
            "account_id": account.account_id,
            "account_number": account.account_number,
            "product_name": account.product_name,
            "total_shares": account.total_shares,
            "total_amount_paid": str(account.total_amount_paid),
            "status": account.status.value
        }
        
    def get_share_account(
        self,
        account_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get share account details
        
        Args:
            account_id: Account ID
            
        Returns:
            Account details
        """
        if not self.share_service:
            return None
        
        account = self.share_service.get_account(account_id)
        
        if not account:
            return None
        
        return {
            "account_id": account.account_id,
            "account_number": account.account_number,
            "client_id": account.client_id,
            "product_name": account.product_name,
            "total_shares": account.total_shares,
            "nominal_value_per_share": str(account.nominal_value_per_share),
            "total_nominal_value": str(account.total_nominal_value),
            "total_amount_paid": str(account.total_amount_paid),
            "total_dividends_paid": str(account.total_dividends_paid),
            "status": account.status.value
        }
        
    def purchase_shares(
        self,
        account_id: str,
        num_shares: int,
        price_per_share: float,
        created_by: str = "ai_agent"
    ) -> Dict[str, Any]:
        """
        Purchase additional shares
        
        Args:
            account_id: Account ID
            num_shares: Number of shares to purchase
            price_per_share: Price per share
            created_by: Creator ID
            
        Returns:
            Transaction details
        """
        from ..modules.shares.models import PurchaseSharesRequest
        
        if not self.share_service:
            return {"error": "Share service not available"}
        
        request = PurchaseSharesRequest(
            account_id=account_id,
            num_shares=num_shares,
            price_per_share=Decimal(str(price_per_share)),
            transaction_date=date.today(),
            created_by=created_by
        )
        
        transaction = self.share_service.purchase_shares(request)
        
        return {
            "transaction_id": transaction.transaction_id,
            "num_shares": transaction.num_shares,
            "price_per_share": str(transaction.price_per_share),
            "total_amount": str(transaction.total_amount),
            "status": transaction.status
        }
        
    # ========================================================================
    # DIVIDEND TOOLS
    # ========================================================================
    
    def declare_dividend(
        self,
        product_id: str,
        dividend_amount_per_share: float,
        record_date: str,
        payment_date: str,
        created_by: str = "ai_agent"
    ) -> Dict[str, Any]:
        """
        Declare dividend for share product
        
        Args:
            product_id: Product ID
            dividend_amount_per_share: Dividend per share
            record_date: Record date (YYYY-MM-DD)
            payment_date: Payment date (YYYY-MM-DD)
            created_by: Creator ID
            
        Returns:
            Dividend declaration details
        """
        from ..modules.shares.models import DeclareDividendRequest
        from datetime import datetime
        
        if not self.share_service:
            return {"error": "Share service not available"}
        
        request = DeclareDividendRequest(
            product_id=product_id,
            dividend_amount_per_share=Decimal(str(dividend_amount_per_share)),
            record_date=datetime.strptime(record_date, "%Y-%m-%d").date(),
            payment_date=datetime.strptime(payment_date, "%Y-%m-%d").date(),
            created_by=created_by
        )
        
        dividend = self.share_service.declare_dividend(request)
        
        return {
            "dividend_id": dividend.dividend_id,
            "product_id": dividend.product_id,
            "dividend_amount_per_share": str(dividend.dividend_amount_per_share),
            "total_dividend_amount": str(dividend.total_dividend_amount),
            "record_date": dividend.record_date.isoformat(),
            "payment_date": dividend.payment_date.isoformat(),
            "status": dividend.status.value
        }
        
    # ========================================================================
    # COB TOOLS
    # ========================================================================
    
    def get_cob_status(
        self,
        business_date: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get COB processing status
        
        Args:
            business_date: Business date (YYYY-MM-DD), defaults to today
            
        Returns:
            COB status
        """
        if not self.cob_engine:
            return None
        
        from datetime import datetime
        
        if business_date:
            target_date = datetime.strptime(business_date, "%Y-%m-%d").date()
        else:
            target_date = date.today()
        
        # Find most recent run for this date
        runs = [r for r in self.cob_engine.runs.values() if r.business_date == target_date]
        
        if not runs:
            return None
        
        run = max(runs, key=lambda x: x.created_at)
        
        return {
            "run_id": run.run_id,
            "business_date": run.business_date.isoformat(),
            "status": run.status.value,
            "total_tasks": run.total_tasks,
            "completed_tasks": run.completed_tasks,
            "failed_tasks": run.failed_tasks,
            "duration_seconds": run.duration_seconds
        }
        
    def trigger_cob(
        self,
        business_date: Optional[str] = None,
        triggered_by: str = "ai_agent"
    ) -> Dict[str, Any]:
        """
        Trigger COB processing
        
        Args:
            business_date: Business date (YYYY-MM-DD), defaults to today
            triggered_by: Trigger source
            
        Returns:
            COB run details
        """
        import asyncio
        from datetime import datetime
        
        if not self.cob_engine:
            return {"error": "COB engine not available"}
        
        if business_date:
            target_date = datetime.strptime(business_date, "%Y-%m-%d").date()
        else:
            target_date = date.today()
        
        # Run COB asynchronously
        run = asyncio.run(self.cob_engine.run_cob(target_date, triggered_by))
        
        return {
            "run_id": run.run_id,
            "business_date": run.business_date.isoformat(),
            "status": run.status.value,
            "message": "COB processing initiated"
        }
        
    # ========================================================================
    # CONFIGURATION TOOLS
    # ========================================================================
    
    def get_config(
        self,
        config_key: str,
        environment: str = "production"
    ) -> Optional[Dict[str, Any]]:
        """
        Get configuration value
        
        Args:
            config_key: Configuration key
            environment: Environment (development, staging, production)
            
        Returns:
            Configuration details
        """
        from ..modules.config.config_manager import ConfigScope, ConfigEnvironment
        
        if not self.config_manager:
            return None
        
        env = ConfigEnvironment(environment)
        config = self.config_manager.get_config(config_key, ConfigScope.GLOBAL, env)
        
        if not config:
            return None
        
        return {
            "config_id": config.config_id,
            "config_key": config.config_key,
            "config_value": config.config_value,
            "config_type": config.config_type,
            "version": config.version,
            "status": config.status.value,
            "description": config.description
        }
        
    def set_config(
        self,
        config_key: str,
        config_value: Any,
        config_type: str = "string",
        environment: str = "production",
        description: Optional[str] = None,
        created_by: str = "ai_agent"
    ) -> Dict[str, Any]:
        """
        Set configuration value
        
        Args:
            config_key: Configuration key
            config_value: Configuration value
            config_type: Value type (string, number, boolean, json)
            environment: Environment
            description: Description
            created_by: Creator ID
            
        Returns:
            Configuration details
        """
        from ..modules.config.config_manager import ConfigScope, ConfigEnvironment
        
        if not self.config_manager:
            return {"error": "Config manager not available"}
        
        env = ConfigEnvironment(environment)
        
        config = self.config_manager.set_config(
            config_key=config_key,
            config_value=config_value,
            config_type=config_type,
            scope=ConfigScope.GLOBAL,
            environment=env,
            description=description,
            created_by=created_by
        )
        
        return {
            "config_id": config.config_id,
            "config_key": config.config_key,
            "config_value": config.config_value,
            "version": config.version,
            "status": config.status.value
        }
        
    def is_feature_enabled(
        self,
        feature_key: str,
        user_id: Optional[str] = None,
        environment: str = "production"
    ) -> bool:
        """
        Check if feature is enabled
        
        Args:
            feature_key: Feature flag key
            user_id: User ID (optional)
            environment: Environment
            
        Returns:
            True if enabled, False otherwise
        """
        from ..modules.config.config_manager import ConfigEnvironment
        
        if not self.config_manager:
            return False
        
        env = ConfigEnvironment(environment)
        
        return self.config_manager.is_feature_enabled(
            flag_key=feature_key,
            user_id=user_id,
            environment=env
        )
        
    def update_feature_flag(
        self,
        feature_key: str,
        is_enabled: Optional[bool] = None,
        rollout_percentage: Optional[int] = None,
        environment: str = "production"
    ) -> Dict[str, Any]:
        """
        Update feature flag
        
        Args:
            feature_key: Feature flag key
            is_enabled: Enable/disable flag
            rollout_percentage: Rollout percentage (0-100)
            environment: Environment
            
        Returns:
            Updated flag details
        """
        from ..modules.config.config_manager import ConfigEnvironment
        
        if not self.config_manager:
            return {"error": "Config manager not available"}
        
        env = ConfigEnvironment(environment)
        
        self.config_manager.update_feature_flag(
            flag_key=feature_key,
            is_enabled=is_enabled,
            rollout_percentage=rollout_percentage,
            environment=env
        )
        
        return {
            "feature_key": feature_key,
            "is_enabled": is_enabled,
            "rollout_percentage": rollout_percentage,
            "message": "Feature flag updated successfully"
        }
