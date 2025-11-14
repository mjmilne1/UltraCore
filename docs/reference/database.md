# UltraCore Database Guide

## 🗄️ Database Architecture

UltraCore uses a **multi-database strategy** leveraging our Event Sourcing and Data Mesh architecture:

### Databases

1. **PostgreSQL** - Primary relational database
   - ACID transactions
   - Customer, Account, Loan data
   - Event Store (event sourcing)
   - Time-series partitioning (transactions)

2. **Redis** (Optional) - Caching layer
   - Session management
   - API response caching
   - Distributed locks

3. **Neo4j** (Optional) - Graph database
   - Customer relationships
   - Beneficial ownership
   - Fraud detection patterns

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Minimal (SQLite for testing)
pip install -r requirements.txt

# With PostgreSQL
pip install -r requirements.txt -r requirements-db.txt

# Everything
pip install -r requirements.txt -r requirements-db.txt -r requirements-monitoring.txt
```

### 2. Configure Database
```bash
# Copy environment template
cp .env.example .env

# Edit .env and set:
# DATABASE_URL=postgresql://user:password@localhost:5432/ultracore
# REDIS_URL=redis://localhost:6379/0  # Optional
# NEO4J_URI=bolt://localhost:7687     # Optional
```

### 3. Initialize Database
```bash
# Create tables
python init_db.py

# Or run migrations
alembic upgrade head
```

### 4. Start API
```bash
python run.py
```

## 📊 Database Schemas

### Data Mesh Organization
```
ultracore/
├── customers/          # Customer domain schema
│   ├── customers
│   └── customer_relationships
├── accounts/          # Account domain schema
│   ├── accounts
│   ├── account_balances
│   └── transactions
└── lending/           # Lending domain schema
    ├── loans
    ├── loan_payments
    ├── loan_payment_schedules
    └── loan_collateral
```

### Event Store
```
event_store            # Immutable event log (all domains)
```

## 🔧 Alembic Migrations

### Create Migration
```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "Add customer table"

# Create empty migration
alembic revision -m "Custom migration"
```

### Apply Migrations
```bash
# Upgrade to latest
alembic upgrade head

# Upgrade one version
alembic upgrade +1

# Downgrade one version
alembic downgrade -1

# Show current version
alembic current

# Show history
alembic history
```

## 💾 Repository Pattern

### Using Repositories
```python
from ultracore.database.config import get_db_manager
from ultracore.database.repositories import CustomerRepository

# Get database session
db_manager = get_db_manager()

async with db_manager.get_async_session() as session:
    # Create repository
    repo = CustomerRepository(session, tenant_id="DEFAULT")
    
    # Query customers
    customer = await repo.get_by_business_id("CUST-123")
    customers = await repo.list(filters={"status": "ACTIVE"})
    
    # Search
    results = await repo.search("john@example.com")
```

### Available Repositories

- **CustomerRepository** - Customer operations
- **AccountRepository** - Account operations
- **TransactionRepository** - Transaction history
- **LoanRepository** - Loan operations
- **LoanPaymentRepository** - Payment tracking

## 🔗 Integration Layer

### Persist Domain Models
```python
from ultracore.database.integration import get_db_integration

async with db_manager.get_async_session() as session:
    integration = get_db_integration(session, tenant_id="DEFAULT")
    
    # Persist customer
    customer_id = await integration.persist_customer(customer, created_by="API")
    
    # Load customer
    customer = await integration.load_customer("CUST-123")
```

## 🎯 Key Features

### Multi-Tenancy

All tables include `tenant_id` for data isolation:
```python
# Automatic tenant filtering
repo = CustomerRepository(session, tenant_id="TENANT-123")
customers = await repo.list()  # Only returns TENANT-123 data
```

### Event Sourcing

All state changes recorded in event store:
```python
# Events automatically emitted on create/update/delete
customer = await repo.create(customer, created_by="API")
# → CustomerCreated event stored

await repo.update(customer, updated_by="API")
# → CustomerUpdated event stored
```

### Soft Deletes

Records marked as deleted, not removed:
```python
# Soft delete
await repo.soft_delete(customer_id, deleted_by="API")

# Include deleted in queries
customers = await repo.list(include_deleted=True)
```

### Caching

Automatic Redis caching (if enabled):
```python
# First call hits database
customer = await repo.get_by_id(customer_id)

# Second call hits cache (3600s TTL)
customer = await repo.get_by_id(customer_id)
```

## 🔍 Performance Optimizations

### Indexes

- Composite indexes on tenant_id + business_id
- Full-text search indexes (pg_trgm)
- Time-series indexes on date fields

### Partitioning

- **Transactions** - Partitioned by transaction_date
- **Events** - Partitioned by event_date

### Connection Pooling
```python
# Configured in DatabaseManager
pool_size=20          # Base connections
max_overflow=40       # Additional connections under load
```

## 🧪 Testing

### Test Database
```bash
# Set test database URL
export DATABASE_URL=postgresql://user:pass@localhost/ultracore_test

# Run tests
pytest tests/
```

### In-Memory SQLite
```python
# For unit tests
database_url = "sqlite:///:memory:"
```

## 📈 Monitoring

### Database Health
```bash
# Check via API
curl http://localhost:8000/api/v1/health/detailed
```

### Query Performance
```python
# Enable SQL logging
from ultracore.database.config import get_db_manager

db_manager = get_db_manager()
db_manager.engine.echo = True  # Log all SQL
```

## 🚨 Troubleshooting

### Connection Errors
```bash
# Check PostgreSQL is running
psql -U user -d ultracore

# Test connection
python -c "from ultracore.database.config import get_db_manager; get_db_manager()"
```

### Migration Errors
```bash
# Reset migrations (DANGER: drops all data)
alembic downgrade base
alembic upgrade head

# Or recreate database
dropdb ultracore
createdb ultracore
python init_db.py
```

### Import Errors
```bash
# Add to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

## 📚 Additional Resources

- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
