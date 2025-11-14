# 📦 Installation Guide

Complete installation guide for UltraCore. This guide covers all installation methods and platform-specific instructions.

---

## 🎯 Installation Methods

Choose the installation method that best fits your needs:

| Method | Best For | Time | Difficulty |
|--------|----------|------|------------|
| **[Docker Compose](#docker-compose-recommended)** | Quick start, development | 10 min | Easy |
| **[Local Development](#local-development)** | Active development, debugging | 20 min | Medium |
| **[Kubernetes](#kubernetes)** | Production deployment | 30 min | Advanced |

---

## 🐳 Docker Compose (Recommended)

The fastest way to get UltraCore running with all dependencies.

### Prerequisites

- Docker 20.10+ and Docker Compose 2.0+
- 4GB RAM minimum, 8GB recommended
- 10GB free disk space

### Installation Steps

```bash
# 1. Clone repository
git clone https://github.com/TuringDynamics3000/UltraCore.git
cd UltraCore

# 2. Start all services
docker-compose up -d

# 3. Wait for services to be healthy (30-60 seconds)
docker-compose ps

# 4. Verify installation
curl http://localhost:8000/health
```

### What's Included

The Docker Compose setup includes:

- **UltraCore API** (port 8000)
- **PostgreSQL** (port 5432)
- **Apache Kafka** (port 9092)
- **Zookeeper** (port 2181)
- **Redis** (port 6379)
- **Kafka UI** (port 8080) - Optional web UI for Kafka

### Configuration

Edit `docker-compose.yml` to customize:

```yaml
services:
  ultracore-api:
    environment:
      - DATABASE_URL=postgresql://ultracore:ultracore@postgres:5432/ultracore
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - REDIS_URL=redis://redis:6379/0
      - API_PORT=8000
```

### Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

---

## 💻 Local Development

Install UltraCore directly on your machine for active development.

### Prerequisites

#### All Platforms
- Python 3.11+
- Git 2.30+
- PostgreSQL 14+
- Apache Kafka 3.0+
- Redis 7.0+

#### Platform-Specific

**macOS:**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.11 postgresql@14 kafka redis git
```

**Ubuntu/Debian:**
```bash
# Update package list
sudo apt update

# Install dependencies
sudo apt install -y python3.11 python3.11-venv postgresql-14 redis-server git

# Install Kafka (requires Java)
sudo apt install -y default-jdk
wget https://downloads.apache.org/kafka/3.6.0/kafka_2.13-3.6.0.tgz
tar -xzf kafka_2.13-3.6.0.tgz
sudo mv kafka_2.13-3.6.0 /opt/kafka
```

**Windows:**
```powershell
# Install Chocolatey if not already installed
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install dependencies
choco install -y python311 postgresql14 redis git

# Kafka on Windows requires manual installation
# Download from: https://kafka.apache.org/downloads
```

### Installation Steps

#### 1. Clone Repository

```bash
git clone https://github.com/TuringDynamics3000/UltraCore.git
cd UltraCore
```

#### 2. Create Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv .venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate

# Windows:
.venv\Scripts\activate
```

#### 3. Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

**requirements.txt:**
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
kafka-python==2.0.2
redis==5.0.1
pydantic==2.5.3
pydantic-settings==2.1.0
alembic==1.13.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
```

**requirements-dev.txt:**
```txt
pytest==7.4.4
pytest-cov==4.1.0
pytest-asyncio==0.23.3
black==24.1.1
flake8==7.0.0
mypy==1.8.0
pre-commit==3.6.0
```

#### 4. Start Infrastructure Services

**PostgreSQL:**
```bash
# macOS:
brew services start postgresql@14

# Ubuntu/Debian:
sudo systemctl start postgresql

# Windows:
# PostgreSQL starts automatically after installation
```

**Kafka:**
```bash
# macOS/Linux:
# Start Zookeeper
/opt/kafka/bin/zookeeper-server-start.sh /opt/kafka/config/zookeeper.properties &

# Start Kafka
/opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/server.properties &

# Windows:
# Start Zookeeper
bin\windows\zookeeper-server-start.bat config\zookeeper.properties

# Start Kafka (in new terminal)
bin\windows\kafka-server-start.bat config\server.properties
```

**Redis:**
```bash
# macOS:
brew services start redis

# Ubuntu/Debian:
sudo systemctl start redis

# Windows:
redis-server
```

#### 5. Configure Database

```bash
# Create database
createdb ultracore

# Or using psql:
psql -U postgres -c "CREATE DATABASE ultracore;"

# Create user (if needed)
psql -U postgres -c "CREATE USER ultracore WITH PASSWORD 'ultracore';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE ultracore TO ultracore;"
```

#### 6. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env
nano .env
```

**.env:**
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
JWT_SECRET=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# External Services
YAHOO_FINANCE_API_KEY=optional
OPENMARKETS_API_KEY=optional
OPENMARKETS_API_SECRET=optional

# Logging
LOG_LEVEL=INFO
```

#### 7. Run Database Migrations

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "Initial schema"

# Apply migrations
alembic upgrade head
```

#### 8. Start UltraCore

```bash
# Start development server
python server.py

# Or use uvicorn directly
uvicorn src.ultracore.main:app --reload --host 0.0.0.0 --port 8000
```

---

## ☸️ Kubernetes

Deploy UltraCore to Kubernetes for production.

### Prerequisites

- Kubernetes cluster (1.24+)
- kubectl configured
- Helm 3.0+
- 8GB RAM minimum per node
- 50GB storage

### Installation Steps

```bash
# 1. Clone repository
git clone https://github.com/TuringDynamics3000/UltraCore.git
cd UltraCore

# 2. Create namespace
kubectl create namespace ultracore

# 3. Install dependencies (Kafka, PostgreSQL, Redis)
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Install PostgreSQL
helm install postgresql bitnami/postgresql \
  --namespace ultracore \
  --set auth.username=ultracore \
  --set auth.password=ultracore \
  --set auth.database=ultracore

# Install Kafka
helm install kafka bitnami/kafka \
  --namespace ultracore \
  --set replicaCount=3

# Install Redis
helm install redis bitnami/redis \
  --namespace ultracore

# 4. Deploy UltraCore
kubectl apply -f k8s/ --namespace ultracore

# 5. Verify deployment
kubectl get pods --namespace ultracore
kubectl get services --namespace ultracore
```

### Configuration

Edit `k8s/configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ultracore-config
data:
  DATABASE_URL: "postgresql://ultracore:ultracore@postgresql:5432/ultracore"
  KAFKA_BOOTSTRAP_SERVERS: "kafka:9092"
  REDIS_URL: "redis://redis:6379/0"
  API_PORT: "8000"
```

### Accessing UltraCore

```bash
# Port forward to access locally
kubectl port-forward service/ultracore-api 8000:8000 --namespace ultracore

# Or create ingress for external access
kubectl apply -f k8s/ingress.yaml --namespace ultracore
```

---

## ✅ Verify Installation

### Check Health Endpoint

```bash
curl http://localhost:8000/health
```

**Expected Response:**
```json
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

### Check API Documentation

Open browser: http://localhost:8000/docs

### Run Tests

```bash
pytest tests/ --cov=src/ultracore
```

**Expected:** 191 tests, 100% pass rate

---

## 🔧 Post-Installation

### 1. Create Admin User

```bash
python scripts/create_admin.py \
  --email admin@example.com \
  --password your-secure-password
```

### 2. Load Sample Data (Optional)

```bash
python scripts/load_sample_data.py
```

### 3. Configure Pre-commit Hooks

```bash
pre-commit install
```

### 4. Verify All Services

```bash
# Check PostgreSQL
psql postgresql://ultracore:ultracore@localhost:5432/ultracore -c "SELECT version();"

# Check Kafka
kafka-topics.sh --list --bootstrap-server localhost:9092

# Check Redis
redis-cli ping
```

---

## 🆘 Troubleshooting

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Database Connection Error

```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Check database exists
psql -U postgres -l | grep ultracore

# Reset database
dropdb ultracore
createdb ultracore
alembic upgrade head
```

### Kafka Connection Error

```bash
# Check Kafka is running
kafka-topics.sh --list --bootstrap-server localhost:9092

# Check Zookeeper is running
echo stat | nc localhost 2181
```

### Redis Connection Error

```bash
# Check Redis is running
redis-cli ping

# Restart Redis
# macOS:
brew services restart redis

# Ubuntu/Debian:
sudo systemctl restart redis
```

---

## 📚 Next Steps

- [Quick Start Guide](quick-start.md) - Make your first API call
- [Development Setup](../development/setup.md) - Configure your IDE
- [Architecture Overview](../architecture/overview.md) - Understand the system

---

## 📞 Get Help

- **Issues:** [GitHub Issues](https://github.com/TuringDynamics3000/UltraCore/issues)
- **Discussions:** [GitHub Discussions](https://github.com/TuringDynamics3000/UltraCore/discussions)
- **Email:** michael@turingdynamics.ai
