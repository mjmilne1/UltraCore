"""
Configuration Management Module

Centralized configuration management with:
- Versioning and audit trail
- Environment-specific configs
- Feature flags
- Dynamic configuration updates
- Configuration validation
- Rollback capabilities
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import json
import uuid


class ConfigScope(str, Enum):
    """Configuration scopes"""
    GLOBAL = "global"
    ORGANIZATION = "organization"
    PRODUCT = "product"
    USER = "user"
    FEATURE = "feature"


class ConfigStatus(str, Enum):
    """Configuration statuses"""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ConfigEnvironment(str, Enum):
    """Deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


# ============================================================================
# MODELS
# ============================================================================

class ConfigurationItem(BaseModel):
    """Individual configuration item"""
    config_id: str
    config_key: str
    config_value: Any
    config_type: str  # string, number, boolean, json, list
    
    # Scope
    scope: ConfigScope
    scope_id: Optional[str] = None  # e.g., product_id, user_id
    
    # Environment
    environment: ConfigEnvironment = ConfigEnvironment.PRODUCTION
    
    # Versioning
    version: int = 1
    is_current: bool = True
    
    # Status
    status: ConfigStatus = ConfigStatus.ACTIVE
    
    # Metadata
    description: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    
    # Validation
    validation_rules: Optional[Dict[str, Any]] = None
    is_encrypted: bool = False
    is_sensitive: bool = False
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    updated_by: str
    
    # History
    previous_version_id: Optional[str] = None
    change_reason: Optional[str] = None


class FeatureFlag(BaseModel):
    """Feature flag for gradual rollout"""
    flag_id: str
    flag_name: str
    flag_key: str
    
    # Status
    is_enabled: bool = False
    
    # Rollout
    rollout_percentage: int = 0  # 0-100
    rollout_users: List[str] = []  # Specific user IDs
    rollout_organizations: List[str] = []  # Specific org IDs
    
    # Environment
    environment: ConfigEnvironment = ConfigEnvironment.PRODUCTION
    
    # Metadata
    description: str
    category: Optional[str] = None
    
    # Dates
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    
    @validator('rollout_percentage')
    def validate_percentage(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Rollout percentage must be between 0 and 100')
        return v


class ConfigurationAudit(BaseModel):
    """Configuration change audit record"""
    audit_id: str
    config_id: str
    config_key: str
    
    # Change details
    action: str  # create, update, delete, rollback
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    
    # Context
    changed_by: str
    changed_at: datetime = Field(default_factory=datetime.utcnow)
    change_reason: Optional[str] = None
    
    # Environment
    environment: ConfigEnvironment
    
    # Request context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


# ============================================================================
# CONFIGURATION MANAGER
# ============================================================================

class ConfigurationManager:
    """
    Configuration Manager
    
    Manages:
    - Configuration items with versioning
    - Feature flags
    - Environment-specific configs
    - Configuration validation
    - Audit trail
    """
    
    def __init__(self, kafka_producer=None):
        self.configs: Dict[str, ConfigurationItem] = {}
        self.feature_flags: Dict[str, FeatureFlag] = {}
        self.audit_log: List[ConfigurationAudit] = []
        self.kafka_producer = kafka_producer
        
        # Initialize default configurations
        self._initialize_defaults()
        
    def _initialize_defaults(self):
        """Initialize default system configurations"""
        
        # Interest calculation method
        self.set_config(
            config_key="interest.calculation_method",
            config_value="daily_balance",
            config_type="string",
            scope=ConfigScope.GLOBAL,
            environment=ConfigEnvironment.PRODUCTION,
            description="Method for calculating interest",
            created_by="system"
        )
        
        # Default currency
        self.set_config(
            config_key="system.default_currency",
            config_value="AUD",
            config_type="string",
            scope=ConfigScope.GLOBAL,
            environment=ConfigEnvironment.PRODUCTION,
            description="Default system currency",
            created_by="system"
        )
        
        # Transaction limits
        self.set_config(
            config_key="transaction.daily_limit",
            config_value=100000.00,
            config_type="number",
            scope=ConfigScope.GLOBAL,
            environment=ConfigEnvironment.PRODUCTION,
            description="Daily transaction limit",
            created_by="system"
        )
        
        # Compliance settings
        self.set_config(
            config_key="compliance.aml_screening_enabled",
            config_value=True,
            config_type="boolean",
            scope=ConfigScope.GLOBAL,
            environment=ConfigEnvironment.PRODUCTION,
            description="Enable AML screening",
            created_by="system"
        )
        
        # Feature flags
        self.create_feature_flag(
            flag_name="AI Credit Scoring",
            flag_key="ai_credit_scoring",
            description="Enable AI-powered credit scoring",
            is_enabled=True,
            rollout_percentage=100,
            created_by="system"
        )
        
    # ========================================================================
    # CONFIGURATION MANAGEMENT
    # ========================================================================
    
    def set_config(
        self,
        config_key: str,
        config_value: Any,
        config_type: str,
        scope: ConfigScope,
        environment: ConfigEnvironment,
        description: Optional[str] = None,
        created_by: str = "system",
        scope_id: Optional[str] = None,
        change_reason: Optional[str] = None
    ) -> ConfigurationItem:
        """Set or update configuration"""
        
        # Check if config exists
        existing = self.get_config(config_key, scope, environment, scope_id)
        
        if existing:
            # Create new version
            return self._update_config(
                existing, config_value, created_by, change_reason
            )
        else:
            # Create new config
            return self._create_config(
                config_key, config_value, config_type, scope,
                environment, description, created_by, scope_id
            )
    
    def _create_config(
        self,
        config_key: str,
        config_value: Any,
        config_type: str,
        scope: ConfigScope,
        environment: ConfigEnvironment,
        description: Optional[str],
        created_by: str,
        scope_id: Optional[str]
    ) -> ConfigurationItem:
        """Create new configuration"""
        config_id = f"CFG-{uuid.uuid4().hex[:12].upper()}"
        
        config = ConfigurationItem(
            config_id=config_id,
            config_key=config_key,
            config_value=config_value,
            config_type=config_type,
            scope=scope,
            scope_id=scope_id,
            environment=environment,
            description=description,
            version=1,
            is_current=True,
            status=ConfigStatus.ACTIVE,
            created_by=created_by,
            updated_by=created_by
        )
        
        self.configs[config_id] = config
        
        # Audit
        self._audit_change(
            config_id, config_key, "create", None, config_value,
            created_by, environment
        )
        
        # Publish event
        if self.kafka_producer:
            self.kafka_producer.publish_config_created(
                config_id, config_key, config_value, environment.value
            )
        
        return config
        
    def _update_config(
        self,
        existing: ConfigurationItem,
        new_value: Any,
        updated_by: str,
        change_reason: Optional[str]
    ) -> ConfigurationItem:
        """Update existing configuration (creates new version)"""
        
        # Mark existing as not current
        existing.is_current = False
        existing.status = ConfigStatus.DEPRECATED
        
        # Create new version
        new_config_id = f"CFG-{uuid.uuid4().hex[:12].upper()}"
        
        new_config = ConfigurationItem(
            config_id=new_config_id,
            config_key=existing.config_key,
            config_value=new_value,
            config_type=existing.config_type,
            scope=existing.scope,
            scope_id=existing.scope_id,
            environment=existing.environment,
            description=existing.description,
            category=existing.category,
            tags=existing.tags,
            validation_rules=existing.validation_rules,
            is_encrypted=existing.is_encrypted,
            is_sensitive=existing.is_sensitive,
            version=existing.version + 1,
            is_current=True,
            status=ConfigStatus.ACTIVE,
            created_by=existing.created_by,
            updated_by=updated_by,
            previous_version_id=existing.config_id,
            change_reason=change_reason
        )
        
        self.configs[new_config_id] = new_config
        
        # Audit
        self._audit_change(
            new_config_id, existing.config_key, "update",
            existing.config_value, new_value, updated_by, existing.environment,
            change_reason
        )
        
        # Publish event
        if self.kafka_producer:
            self.kafka_producer.publish_config_updated(
                new_config_id, existing.config_key, existing.config_value,
                new_value, existing.environment.value
            )
        
        return new_config
        
    def get_config(
        self,
        config_key: str,
        scope: ConfigScope,
        environment: ConfigEnvironment,
        scope_id: Optional[str] = None
    ) -> Optional[ConfigurationItem]:
        """Get current configuration value"""
        for config in self.configs.values():
            if (config.config_key == config_key and
                config.scope == scope and
                config.environment == environment and
                config.scope_id == scope_id and
                config.is_current and
                config.status == ConfigStatus.ACTIVE):
                return config
        return None
        
    def get_config_value(
        self,
        config_key: str,
        scope: ConfigScope = ConfigScope.GLOBAL,
        environment: ConfigEnvironment = ConfigEnvironment.PRODUCTION,
        scope_id: Optional[str] = None,
        default: Any = None
    ) -> Any:
        """Get configuration value (convenience method)"""
        config = self.get_config(config_key, scope, environment, scope_id)
        return config.config_value if config else default
        
    def get_config_history(
        self,
        config_key: str,
        scope: ConfigScope,
        environment: ConfigEnvironment
    ) -> List[ConfigurationItem]:
        """Get all versions of a configuration"""
        history = [
            c for c in self.configs.values()
            if c.config_key == config_key and
               c.scope == scope and
               c.environment == environment
        ]
        return sorted(history, key=lambda x: x.version, reverse=True)
        
    def rollback_config(
        self,
        config_key: str,
        scope: ConfigScope,
        environment: ConfigEnvironment,
        target_version: int,
        rolled_back_by: str,
        reason: str
    ) -> ConfigurationItem:
        """Rollback configuration to previous version"""
        
        # Get target version
        history = self.get_config_history(config_key, scope, environment)
        target = next((c for c in history if c.version == target_version), None)
        
        if not target:
            raise ValueError(f"Version {target_version} not found")
        
        # Get current version
        current = self.get_config(config_key, scope, environment)
        
        if not current:
            raise ValueError("No current version found")
        
        # Create new version with old value
        return self._update_config(
            current, target.config_value, rolled_back_by,
            f"Rollback to version {target_version}: {reason}"
        )
        
    # ========================================================================
    # FEATURE FLAGS
    # ========================================================================
    
    def create_feature_flag(
        self,
        flag_name: str,
        flag_key: str,
        description: str,
        is_enabled: bool = False,
        rollout_percentage: int = 0,
        environment: ConfigEnvironment = ConfigEnvironment.PRODUCTION,
        created_by: str = "system"
    ) -> FeatureFlag:
        """Create feature flag"""
        flag_id = f"FF-{uuid.uuid4().hex[:12].upper()}"
        
        flag = FeatureFlag(
            flag_id=flag_id,
            flag_name=flag_name,
            flag_key=flag_key,
            description=description,
            is_enabled=is_enabled,
            rollout_percentage=rollout_percentage,
            environment=environment,
            created_by=created_by
        )
        
        self.feature_flags[flag_id] = flag
        
        # Publish event
        if self.kafka_producer:
            self.kafka_producer.publish_feature_flag_created(
                flag_id, flag_key, is_enabled, rollout_percentage
            )
        
        return flag
        
    def is_feature_enabled(
        self,
        flag_key: str,
        user_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        environment: ConfigEnvironment = ConfigEnvironment.PRODUCTION
    ) -> bool:
        """Check if feature is enabled for user/org"""
        
        # Find flag
        flag = next(
            (f for f in self.feature_flags.values()
             if f.flag_key == flag_key and f.environment == environment),
            None
        )
        
        if not flag:
            return False
        
        if not flag.is_enabled:
            return False
        
        # Check specific user
        if user_id and user_id in flag.rollout_users:
            return True
        
        # Check specific organization
        if organization_id and organization_id in flag.rollout_organizations:
            return True
        
        # Check rollout percentage
        if flag.rollout_percentage >= 100:
            return True
        
        if flag.rollout_percentage == 0:
            return False
        
        # Hash-based rollout (deterministic)
        if user_id:
            user_hash = hash(user_id) % 100
            return user_hash < flag.rollout_percentage
        
        return False
        
    def update_feature_flag(
        self,
        flag_key: str,
        is_enabled: Optional[bool] = None,
        rollout_percentage: Optional[int] = None,
        environment: ConfigEnvironment = ConfigEnvironment.PRODUCTION
    ):
        """Update feature flag"""
        flag = next(
            (f for f in self.feature_flags.values()
             if f.flag_key == flag_key and f.environment == environment),
            None
        )
        
        if not flag:
            raise ValueError(f"Feature flag {flag_key} not found")
        
        if is_enabled is not None:
            flag.is_enabled = is_enabled
        
        if rollout_percentage is not None:
            flag.rollout_percentage = rollout_percentage
        
        flag.updated_at = datetime.now(timezone.utc)
        
        # Publish event
        if self.kafka_producer:
            self.kafka_producer.publish_feature_flag_updated(
                flag.flag_id, flag_key, flag.is_enabled, flag.rollout_percentage
            )
        
    # ========================================================================
    # AUDIT
    # ========================================================================
    
    def _audit_change(
        self,
        config_id: str,
        config_key: str,
        action: str,
        old_value: Any,
        new_value: Any,
        changed_by: str,
        environment: ConfigEnvironment,
        change_reason: Optional[str] = None
    ):
        """Record configuration change in audit log"""
        audit_id = f"AUDIT-{uuid.uuid4().hex[:12].upper()}"
        
        audit = ConfigurationAudit(
            audit_id=audit_id,
            config_id=config_id,
            config_key=config_key,
            action=action,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
            environment=environment,
            change_reason=change_reason
        )
        
        self.audit_log.append(audit)
        
        # Publish event
        if self.kafka_producer:
            self.kafka_producer.publish_config_audit(
                audit_id, config_key, action, changed_by
            )
        
    def get_audit_log(
        self,
        config_key: Optional[str] = None,
        changed_by: Optional[str] = None,
        limit: int = 100
    ) -> List[ConfigurationAudit]:
        """Get audit log"""
        filtered = self.audit_log
        
        if config_key:
            filtered = [a for a in filtered if a.config_key == config_key]
        
        if changed_by:
            filtered = [a for a in filtered if a.changed_by == changed_by]
        
        return sorted(filtered, key=lambda x: x.changed_at, reverse=True)[:limit]
