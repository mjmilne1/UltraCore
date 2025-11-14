# 🚀 Quick Start Guide

Get UltraCore running on your machine in **under 30 minutes**. This guide walks you through installation, setup, and running your first API call.

---

## ⏱️ Time Estimate

- **Prerequisites:** 5 minutes (if already installed)
- **Installation:** 10 minutes
- **First API Call:** 5 minutes
- **Explore Features:** 10 minutes

**Total:** ~30 minutes

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

### Required Software

| Software | Version | Installation |
|----------|---------|--------------|
| **Python** | 3.11+ | [python.org](https://www.python.org/downloads/) |
| **Docker** | 20.10+ | [docker.com](https://docs.docker.com/get-docker/) |
| **Docker Compose** | 2.0+ | Included with Docker Desktop |
| **Git** | 2.30+ | [git-scm.com](https://git-scm.com/downloads) |

### Verify Installation

```bash
# Check Python version
python3.11 --version
# Expected: Python 3.11.0 or higher

# Check Docker version
docker --version
# Expected: Docker version 20.10.0 or higher

# Check Docker Compose version
docker-compose --version
# Expected: Docker Compose version 2.0.0 or higher

# Check Git version
git --version
# Expected: git version 2.30.0 or higher
```

### Optional (Recommended)

- **IDE:** VS Code, PyCharm, or your preferred editor
- **GitHub CLI:** `gh` for easier GitHub operations
- **PostgreSQL Client:** `psql` for database inspection

---

## 📦 Installation

### Step 1: Clone the Repository

```bash
# Clone UltraCore repository
git clone https://github.com/TuringDynamics3000/UltraCore.git

# Navigate to project directory
cd UltraCore

# Verify you're in the right directory
ls -la
# You should see: README.md, docs/, src/, tests/, etc.
```

### Step 2: Create Python Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate

# Verify activation (prompt should show (.venv))
which python
# Expected: /path/to/UltraCore/.venv/bin/python
```

### Step 3: Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi
# Expected: fastapi 0.109.0 or similar
```

**Common Issues:**
- If `requirements.txt` is missing, create it with essential dependencies:
  ```bash
  pip install fastapi uvicorn sqlalchemy psycopg2-binary kafka-python redis pydantic
  ```

### Step 4: Start Infrastructure Services

UltraCore requires Kafka, PostgreSQL, and Redis. We use Docker Compose to run these services:

```bash
# Start infrastructure services
docker-compose up -d

# Verify services are running
docker-compose ps
# Expected: kafka, postgresql, redis all "Up"

# Check service health
docker-compose logs --tail=50
```

**Services Started:**
- **Kafka** - Event bus (port 9092)
- **Zookeeper** - Kafka coordination (port 2181)
- **PostgreSQL** - Database (port 5432)
- **Redis** - Cache (port 6379)

**Troubleshooting:**
- If ports are already in use, see [Troubleshooting Guide](troubleshooting.md#port-conflicts)
- If Docker fails to start, ensure Docker Desktop is running

### Step 5: Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env  # or use your preferred editor
```

**Required Environment Variables:**

```bash
# Database
DATABASE_URL=postgresql://ultracore:ultracore@localhost:5432/ultracore

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# Redis
REDIS_URL=redis://localhost:6379/0

# API
API_HOST=0.0.0.0
API_PORT=8000

# Security
JWT_SECRET=your-secret-key-here-change-in-production
```

**Note:** For development, the default values in `.env.example` are sufficient.

### Step 6: Initialize Database

```bash
# Run database migrations
alembic upgrade head

# Verify database is initialized
psql postgresql://ultracore:ultracore@localhost:5432/ultracore -c "\dt"
# Expected: List of tables (accounts, transactions, holdings, etc.)
```

**If Alembic is not configured:**
```bash
# Initialize Alembic
alembic init alembic

# Create first migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head
```

### Step 7: Start UltraCore API

```bash
# Start development server
python server.py

# Or use uvicorn directly
uvicorn src.ultracore.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## ✅ Verify Installation

### Check API Health

```bash
# Check health endpoint
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "kafka": "connected",
    "redis": "connected"
  }
}
```

### Access API Documentation

Open your browser and navigate to:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

You should see the interactive API documentation with all available endpoints.

---

## 🎯 Your First API Call

Let's create a tenant, user, and account to verify everything works:

### 1. Create a Tenant

```bash
curl -X POST http://localhost:8000/api/v1/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Demo Bank",
    "identifier": "demo-bank",
    "timezone": "Australia/Sydney"
  }'
```

**Expected Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Demo Bank",
  "identifier": "demo-bank",
  "timezone": "Australia/Sydney",
  "created_at": "2024-11-14T10:00:00Z"
}
```

### 2. Create a User

```bash
curl -X POST http://localhost:8000/api/v1/users \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "demo@example.com",
    "first_name": "Demo",
    "last_name": "User"
  }'
```

### 3. Create an Account

```bash
curl -X POST http://localhost:8000/api/v1/accounts \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "USER_ID_FROM_STEP_2",
    "account_type": "savings",
    "currency": "AUD",
    "initial_balance": 1000.00
  }'
```

### 4. Check Account Balance

```bash
curl http://localhost:8000/api/v1/accounts/ACCOUNT_ID_FROM_STEP_3
```

**Expected Response:**
```json
{
  "id": "ACCOUNT_ID",
  "account_type": "savings",
  "currency": "AUD",
  "balance": 1000.00,
  "status": "active"
}
```

🎉 **Congratulations!** You've successfully:
- Installed UltraCore
- Started all services
- Created a tenant, user, and account
- Made your first API call

---

## 🔍 Explore Features

Now that UltraCore is running, explore these features:

### 1. Event Sourcing

Check Kafka events:

```bash
# View Kafka topics
docker exec -it ultracore-kafka kafka-topics --list --bootstrap-server localhost:9092

# Consume events from a topic
docker exec -it ultracore-kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic ultracore.accounts \
  --from-beginning
```

### 2. Investment Pods

Create a goal-based investment pod:

```bash
curl -X POST http://localhost:8000/api/v1/investment-pods \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "YOUR_TENANT_ID",
    "user_id": "YOUR_USER_ID",
    "goal": "first_home",
    "target_amount": 100000.00,
    "target_date": "2030-01-01",
    "risk_tolerance": "moderate"
  }'
```

### 3. Trading

Place a market order:

```bash
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_id": "YOUR_TENANT_ID",
    "account_id": "YOUR_ACCOUNT_ID",
    "symbol": "VAS.AX",
    "side": "buy",
    "quantity": 10,
    "order_type": "market"
  }'
```

### 4. Multi-Currency

Convert currency:

```bash
curl -X POST http://localhost:8000/api/v1/fx/convert \
  -H "Content-Type: application/json" \
  -d '{
    "from_currency": "AUD",
    "to_currency": "USD",
    "amount": 1000.00
  }'
```

---

## 🧪 Run Tests

Verify your installation by running the test suite:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/ultracore --cov-report=html

# Run specific test suite
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/
```

**Expected:** 191 tests, 100% pass rate

---

## 📚 Next Steps

Now that you have UltraCore running, here's what to do next:

### Learn More
- [Architecture Overview](../architecture/overview.md) - Understand the system design
- [API Documentation](../api/rest-api.md) - Explore all API endpoints
- [Module Documentation](../modules/README.md) - Deep dive into banking modules

### Start Developing
- [Development Setup](../development/setup.md) - Configure your IDE and tools
- [Contributing Guide](../development/contributing.md) - Make your first contribution
- [Coding Standards](../development/coding-standards.md) - Follow our style guide

### Deploy
- [Docker Deployment](../deployment/docker.md) - Deploy with Docker
- [Kubernetes Deployment](../deployment/kubernetes.md) - Deploy to Kubernetes

---

## 🆘 Troubleshooting

Having issues? Check our [Troubleshooting Guide](troubleshooting.md) for common problems and solutions:

- [Port Conflicts](troubleshooting.md#port-conflicts)
- [Docker Issues](troubleshooting.md#docker-issues)
- [Database Connection Errors](troubleshooting.md#database-errors)
- [Kafka Connection Errors](troubleshooting.md#kafka-errors)

Still stuck? [Open a GitHub Issue](https://github.com/TuringDynamics3000/UltraCore/issues) or ask in [Discussions](https://github.com/TuringDynamics3000/UltraCore/discussions).

---

## 📞 Get Help

- **Documentation:** [docs/](../README.md)
- **Issues:** [GitHub Issues](https://github.com/TuringDynamics3000/UltraCore/issues)
- **Discussions:** [GitHub Discussions](https://github.com/TuringDynamics3000/UltraCore/discussions)
- **Email:** michael@turingdynamics.ai

---

**Welcome to UltraCore!** 🎉

You're now ready to start building with UltraCore. Happy coding!
