# Production Security & Database Architecture

## Overview

This document outlines the production-grade security and database architecture for UltraCore, implementing bank-grade security controls, persistent data storage, and deployment-ready infrastructure.

---

## Security Architecture

### 1. Secrets Management

**Environment-Based Configuration:**
- All secrets externalized to environment variables
- No hardcoded credentials in codebase
- Support for `.env` files (development)
- Support for cloud secret managers (production: AWS Secrets Manager, Azure Key Vault)

**Secrets to Externalize:**
```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/ultracore
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# JWT
JWT_SECRET_KEY=<random-256-bit-key>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# MFA
MFA_ISSUER=UltraCore
MFA_TOTP_INTERVAL=30

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_SECURITY_PROTOCOL=SASL_SSL
KAFKA_SASL_MECHANISM=PLAIN
KAFKA_SASL_USERNAME=<username>
KAFKA_SASL_PASSWORD=<password>

# Redis
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=<password>

# Encryption
ENCRYPTION_KEY=<random-256-bit-key>
FIELD_ENCRYPTION_KEY=<random-256-bit-key>

# API Security
API_RATE_LIMIT_PER_MINUTE=60
API_RATE_LIMIT_PER_HOUR=1000
CORS_ORIGINS=https://app.ultracore.com

# Monitoring
SENTRY_DSN=<sentry-dsn>
LOG_LEVEL=INFO
```

### 2. Multi-Factor Authentication (MFA)

**TOTP-Based MFA:**
- Time-based One-Time Password (RFC 6238)
- 30-second time window
- 6-digit codes
- QR code generation for authenticator apps
- Backup codes for account recovery

**MFA Flow:**
```
1. User enables MFA
   ↓
2. System generates TOTP secret
   ↓
3. QR code displayed (scan with Google Authenticator, Authy, etc.)
   ↓
4. User verifies with first code
   ↓
5. Backup codes generated and displayed
   ↓
6. MFA enabled

Login with MFA:
1. Username + password authentication
   ↓
2. System checks if MFA enabled
   ↓
3. Request TOTP code
   ↓
4. Verify TOTP code
   ↓
5. Issue JWT tokens
```

**Backup Codes:**
- 10 single-use backup codes
- Hashed and stored securely
- Used when TOTP device unavailable
- Regenerate after use

### 3. Role-Based Access Control (RBAC)

**Roles:**
```python
class Role(str, Enum):
    SUPER_ADMIN = "super_admin"      # Full system access
    ADMIN = "admin"                   # Tenant admin
    MANAGER = "manager"               # Department manager
    OFFICER = "officer"               # Loan officer, account manager
    CUSTOMER_SERVICE = "customer_service"  # Customer support
    AUDITOR = "auditor"               # Read-only audit access
    CUSTOMER = "customer"             # End customer
```

**Permissions:**
```python
class Permission(str, Enum):
    # Users
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # Accounts
    ACCOUNT_CREATE = "account:create"
    ACCOUNT_READ = "account:read"
    ACCOUNT_UPDATE = "account:update"
    ACCOUNT_DELETE = "account:delete"
    ACCOUNT_APPROVE = "account:approve"
    
    # Transactions
    TRANSACTION_CREATE = "transaction:create"
    TRANSACTION_READ = "transaction:read"
    TRANSACTION_APPROVE = "transaction:approve"
    TRANSACTION_REVERSE = "transaction:reverse"
    
    # Loans
    LOAN_CREATE = "loan:create"
    LOAN_READ = "loan:read"
    LOAN_UPDATE = "loan:update"
    LOAN_APPROVE = "loan:approve"
    LOAN_DISBURSE = "loan:disburse"
    
    # Reports
    REPORT_VIEW = "report:view"
    REPORT_EXPORT = "report:export"
    
    # Settings
    SETTINGS_VIEW = "settings:view"
    SETTINGS_UPDATE = "settings:update"
```

**Role-Permission Matrix:**
| Permission | Super Admin | Admin | Manager | Officer | Customer Service | Auditor | Customer |
|------------|-------------|-------|---------|---------|------------------|---------|----------|
| user:create | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| user:read | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | Own only |
| account:create | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| account:approve | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| transaction:approve | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| loan:approve | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| report:view | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |

### 4. Rate Limiting

**Rate Limit Tiers:**
```python
# Per-endpoint rate limits
RATE_LIMITS = {
    "auth": "5/minute",           # Login attempts
    "mfa": "3/minute",            # MFA verification
    "api_default": "60/minute",   # Default API rate
    "api_read": "100/minute",     # Read operations
    "api_write": "30/minute",     # Write operations
    "api_admin": "200/minute",    # Admin operations
}
```

**Implementation:**
- Redis-backed rate limiting
- Per-user and per-IP tracking
- Sliding window algorithm
- HTTP 429 (Too Many Requests) response
- Retry-After header

### 5. Additional Security Controls

**Password Policy:**
- Minimum 12 characters
- Must contain: uppercase, lowercase, number, special character
- Password history (prevent reuse of last 5 passwords)
- Maximum age: 90 days
- Bcrypt hashing with cost factor 12

**Session Management:**
- JWT-based stateless authentication
- Access token: 30 minutes
- Refresh token: 7 days
- Token rotation on refresh
- Blacklist for revoked tokens (Redis)

**API Security:**
- HTTPS only (TLS 1.3)
- CORS with whitelist
- CSRF protection
- Request signing for sensitive operations
- Input validation and sanitization

**Audit Logging:**
- All authentication attempts
- All authorization failures
- All data modifications
- All admin actions
- Immutable audit log (append-only)

---

## Database Architecture

### 1. PostgreSQL Schema Design

**Multi-Tenant Architecture:**
```sql
-- All tables include tenant_id for data isolation
CREATE TABLE accounts (
    account_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    customer_id UUID NOT NULL,
    -- ... other fields
    CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id)
);

-- Row-level security (RLS) for tenant isolation
ALTER TABLE accounts ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON accounts
    USING (tenant_id = current_setting('app.current_tenant')::UUID);
```

**Domain Tables:**

**1. Users & Authentication:**
```sql
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE mfa_backup_codes (
    code_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    code_hash VARCHAR(255) NOT NULL,
    used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE refresh_tokens (
    token_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

**2. Savings Accounts:**
```sql
CREATE TABLE savings_accounts (
    account_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    customer_id UUID NOT NULL,
    account_number VARCHAR(50) UNIQUE NOT NULL,
    account_type VARCHAR(50) NOT NULL,
    balance DECIMAL(19, 4) NOT NULL DEFAULT 0,
    available_balance DECIMAL(19, 4) NOT NULL DEFAULT 0,
    interest_rate DECIMAL(5, 2),
    status VARCHAR(50) NOT NULL,
    opened_date DATE NOT NULL,
    closed_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);

CREATE INDEX idx_savings_tenant ON savings_accounts(tenant_id);
CREATE INDEX idx_savings_customer ON savings_accounts(customer_id);
CREATE INDEX idx_savings_status ON savings_accounts(status);
```

**3. Transactions:**
```sql
CREATE TABLE transactions (
    transaction_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    account_id UUID NOT NULL,
    transaction_type VARCHAR(50) NOT NULL,
    amount DECIMAL(19, 4) NOT NULL,
    balance_after DECIMAL(19, 4) NOT NULL,
    description TEXT,
    reference VARCHAR(255),
    transaction_date TIMESTAMP NOT NULL,
    posted_date TIMESTAMP,
    status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id),
    FOREIGN KEY (account_id) REFERENCES savings_accounts(account_id)
);

CREATE INDEX idx_transactions_tenant ON transactions(tenant_id);
CREATE INDEX idx_transactions_account ON transactions(account_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);
```

**4. Recurring Deposits:**
```sql
CREATE TABLE recurring_deposits (
    recurring_deposit_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    account_id UUID NOT NULL,
    customer_id UUID NOT NULL,
    deposit_amount DECIMAL(19, 4) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    next_deposit_date DATE,
    interest_rate DECIMAL(5, 2) NOT NULL,
    status VARCHAR(50) NOT NULL,
    total_deposits_made INTEGER DEFAULT 0,
    total_amount_deposited DECIMAL(19, 4) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id),
    FOREIGN KEY (account_id) REFERENCES savings_accounts(account_id)
);
```

**5. Standing Orders:**
```sql
CREATE TABLE standing_orders (
    standing_order_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    from_account_id UUID NOT NULL,
    to_account_id UUID,
    customer_id UUID NOT NULL,
    amount DECIMAL(19, 4) NOT NULL,
    frequency VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    next_execution_date DATE,
    status VARCHAR(50) NOT NULL,
    total_executions INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id),
    FOREIGN KEY (from_account_id) REFERENCES savings_accounts(account_id)
);
```

**6. Savings Buckets:**
```sql
CREATE TABLE savings_buckets (
    bucket_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    account_id UUID NOT NULL,
    customer_id UUID NOT NULL,
    goal_type VARCHAR(50) NOT NULL,
    goal_name VARCHAR(255) NOT NULL,
    target_amount DECIMAL(19, 4) NOT NULL,
    current_balance DECIMAL(19, 4) DEFAULT 0,
    target_date DATE,
    status VARCHAR(50) NOT NULL,
    allocation_percentage DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id),
    FOREIGN KEY (account_id) REFERENCES savings_accounts(account_id)
);
```

**7. Audit Log:**
```sql
CREATE TABLE audit_log (
    audit_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    user_id UUID,
    action VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_tenant ON audit_log(tenant_id);
CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
```

### 2. Database Repositories

**Repository Pattern:**
```python
class BaseRepository:
    """Base repository with common CRUD operations"""
    
    async def create(self, entity: BaseModel) -> BaseModel:
        """Create entity"""
    
    async def get(self, id: UUID) -> Optional[BaseModel]:
        """Get entity by ID"""
    
    async def update(self, id: UUID, entity: BaseModel) -> BaseModel:
        """Update entity"""
    
    async def delete(self, id: UUID) -> bool:
        """Delete entity"""
    
    async def list(self, filters: dict) -> List[BaseModel]:
        """List entities with filters"""

class SavingsAccountRepository(BaseRepository):
    """Savings account repository"""
    
    async def get_by_account_number(self, account_number: str) -> Optional[SavingsAccount]:
        """Get account by account number"""
    
    async def get_by_customer(self, customer_id: UUID) -> List[SavingsAccount]:
        """Get all accounts for customer"""
    
    async def update_balance(self, account_id: UUID, amount: Decimal) -> SavingsAccount:
        """Update account balance"""
```

### 3. Alembic Migrations

**Migration Structure:**
```
alembic/
├── versions/
│   ├── 001_initial_schema.py
│   ├── 002_add_mfa_tables.py
│   ├── 003_add_savings_tables.py
│   ├── 004_add_recurring_deposits.py
│   ├── 005_add_standing_orders.py
│   └── 006_add_savings_buckets.py
├── env.py
└── script.py.mako
```

**Migration Commands:**
```bash
# Create new migration
alembic revision --autogenerate -m "Add savings tables"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history
```

---

## Deployment Architecture

### 1. Environment Configuration

**Development:**
```bash
ENV=development
DEBUG=True
DATABASE_URL=postgresql+asyncpg://dev:dev@localhost:5432/ultracore_dev
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

**Staging:**
```bash
ENV=staging
DEBUG=False
DATABASE_URL=postgresql+asyncpg://staging:***@db-staging:5432/ultracore_staging
KAFKA_BOOTSTRAP_SERVERS=kafka-staging:9092
```

**Production:**
```bash
ENV=production
DEBUG=False
DATABASE_URL=postgresql+asyncpg://prod:***@db-prod:5432/ultracore_prod
KAFKA_BOOTSTRAP_SERVERS=kafka-prod-1:9092,kafka-prod-2:9092,kafka-prod-3:9092
```

### 2. Security Hardening

**Application:**
- Run as non-root user
- Minimal container image (distroless)
- No shell access in production containers
- Read-only filesystem where possible

**Database:**
- SSL/TLS connections only
- Connection pooling (20 connections, 10 overflow)
- Prepared statements (SQL injection prevention)
- Row-level security (RLS) for tenant isolation

**Network:**
- Private VPC/VNET
- Security groups/NSGs
- No public database access
- API gateway/load balancer only

---

## Conclusion

This architecture provides bank-grade security and data persistence for UltraCore, ready for production deployment with comprehensive security controls, persistent data storage, and enterprise-grade infrastructure.
