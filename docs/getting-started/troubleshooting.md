# 🔧 Troubleshooting Guide

Common problems and solutions for UltraCore. If you don't find your issue here, [open a GitHub issue](https://github.com/TuringDynamics3000/UltraCore/issues).

---

## 📋 Quick Diagnosis

Run this command to check your environment:

```bash
# Check all services
./scripts/check_health.sh

# Or manually:
curl http://localhost:8000/health
```

---

## 🐳 Docker Issues

### Docker Daemon Not Running

**Symptoms:**
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Solution:**
```bash
# macOS:
open -a Docker

# Linux:
sudo systemctl start docker

# Windows:
# Start Docker Desktop from Start Menu
```

### Port Already in Use

**Symptoms:**
```
Error starting userland proxy: listen tcp4 0.0.0.0:8000: bind: address already in use
```

**Solution:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or change UltraCore port in docker-compose.yml:
services:
  ultracore-api:
    ports:
      - "8001:8000"  # Use port 8001 instead
```

### Docker Compose Services Won't Start

**Symptoms:**
```
ERROR: Service 'kafka' failed to build
```

**Solution:**
```bash
# Remove all containers and volumes
docker-compose down -v

# Remove Docker images
docker-compose rm -f

# Rebuild and start
docker-compose up --build -d

# Check logs
docker-compose logs --tail=100
```

### Out of Disk Space

**Symptoms:**
```
no space left on device
```

**Solution:**
```bash
# Clean up Docker
docker system prune -a --volumes

# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune
```

---

## 🗄️ Database Errors

### Connection Refused

**Symptoms:**
```
psycopg2.OperationalError: could not connect to server: Connection refused
```

**Solution:**
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Start PostgreSQL
# macOS:
brew services start postgresql@14

# Linux:
sudo systemctl start postgresql

# Docker:
docker-compose up -d postgres
```

### Database Does Not Exist

**Symptoms:**
```
psycopg2.OperationalError: FATAL: database "ultracore" does not exist
```

**Solution:**
```bash
# Create database
createdb ultracore

# Or using psql:
psql -U postgres -c "CREATE DATABASE ultracore;"

# Run migrations
alembic upgrade head
```

### Authentication Failed

**Symptoms:**
```
psycopg2.OperationalError: FATAL: password authentication failed for user "ultracore"
```

**Solution:**
```bash
# Reset user password
psql -U postgres -c "ALTER USER ultracore WITH PASSWORD 'ultracore';"

# Or create user if doesn't exist:
psql -U postgres -c "CREATE USER ultracore WITH PASSWORD 'ultracore';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE ultracore TO ultracore;"

# Update .env file
DATABASE_URL=postgresql://ultracore:ultracore@localhost:5432/ultracore
```

### Migration Errors

**Symptoms:**
```
alembic.util.exc.CommandError: Can't locate revision identified by 'abc123'
```

**Solution:**
```bash
# Check current migration version
alembic current

# Reset database (WARNING: deletes all data)
dropdb ultracore
createdb ultracore

# Re-run migrations
alembic upgrade head

# Or stamp to specific version:
alembic stamp head
```

### Table Already Exists

**Symptoms:**
```
psycopg2.errors.DuplicateTable: relation "accounts" already exists
```

**Solution:**
```bash
# Option 1: Drop and recreate (WARNING: deletes data)
dropdb ultracore
createdb ultracore
alembic upgrade head

# Option 2: Stamp current state
alembic stamp head
```

---

## 📨 Kafka Errors

### Connection Timeout

**Symptoms:**
```
kafka.errors.KafkaTimeoutError: Failed to update metadata after 60.0 secs
```

**Solution:**
```bash
# Check Kafka is running
docker-compose ps kafka

# Check Kafka logs
docker-compose logs kafka --tail=100

# Restart Kafka
docker-compose restart kafka

# Wait for Kafka to be ready (30-60 seconds)
sleep 60
```

### Broker Not Available

**Symptoms:**
```
kafka.errors.NoBrokersAvailable: NoBrokersAvailable
```

**Solution:**
```bash
# Check Zookeeper is running
docker-compose ps zookeeper

# Restart Kafka and Zookeeper
docker-compose restart zookeeper kafka

# Verify Kafka topics
docker exec -it ultracore-kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Topic Does Not Exist

**Symptoms:**
```
kafka.errors.UnknownTopicOrPartitionError: This server does not host this topic-partition
```

**Solution:**
```bash
# Create topic manually
docker exec -it ultracore-kafka kafka-topics \
  --create \
  --topic ultracore.accounts \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1

# Or let UltraCore auto-create topics (set in .env):
KAFKA_AUTO_CREATE_TOPICS=true
```

### Consumer Group Lag

**Symptoms:**
- Events not being processed
- Old events piling up

**Solution:**
```bash
# Check consumer group lag
docker exec -it ultracore-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group ultracore-consumers

# Reset consumer group offset (WARNING: reprocesses events)
docker exec -it ultracore-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group ultracore-consumers \
  --reset-offsets \
  --to-earliest \
  --execute \
  --all-topics
```

---

## 🔴 Redis Errors

### Connection Refused

**Symptoms:**
```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379. Connection refused.
```

**Solution:**
```bash
# Check Redis is running
redis-cli ping

# Start Redis
# macOS:
brew services start redis

# Linux:
sudo systemctl start redis

# Docker:
docker-compose up -d redis
```

### Out of Memory

**Symptoms:**
```
redis.exceptions.ResponseError: OOM command not allowed when used memory > 'maxmemory'
```

**Solution:**
```bash
# Check Redis memory usage
redis-cli info memory

# Increase max memory in redis.conf:
maxmemory 2gb
maxmemory-policy allkeys-lru

# Or flush Redis (WARNING: deletes all cached data)
redis-cli FLUSHALL
```

---

## 🐍 Python Errors

### Module Not Found

**Symptoms:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Ensure virtual environment is activated
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi
```

### Import Error

**Symptoms:**
```
ImportError: cannot import name 'AccountService' from 'ultracore.domains.accounting'
```

**Solution:**
```bash
# Check PYTHONPATH
echo $PYTHONPATH

# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/UltraCore"

# Or install in editable mode
pip install -e .
```

### Version Conflicts

**Symptoms:**
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed
```

**Solution:**
```bash
# Create fresh virtual environment
deactivate
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 🧪 Test Failures

### Tests Fail Locally

**Symptoms:**
```
FAILED tests/unit/accounting/test_account_service.py::test_create_account
```

**Solution:**
```bash
# Run tests with verbose output
pytest tests/ -v

# Run specific test
pytest tests/unit/accounting/test_account_service.py::test_create_account -v

# Check test dependencies
pip install -r requirements-dev.txt

# Clear pytest cache
pytest --cache-clear
```

### Database Not Clean Between Tests

**Symptoms:**
- Tests pass individually but fail when run together
- "Duplicate key" errors

**Solution:**
```bash
# Use pytest fixtures for database cleanup
# Add to conftest.py:
@pytest.fixture(autouse=True)
def cleanup_database(db_session):
    yield
    db_session.rollback()
    db_session.close()

# Or use test database
DATABASE_URL=postgresql://ultracore:ultracore@localhost:5432/ultracore_test pytest tests/
```

### Coverage Too Low

**Symptoms:**
```
FAILED: Required coverage of 80% not reached. Total coverage: 65.23%
```

**Solution:**
```bash
# Generate coverage report
pytest tests/ --cov=src/ultracore --cov-report=html

# Open report
open htmlcov/index.html

# Add tests for uncovered lines
```

---

## 🌐 API Errors

### 404 Not Found

**Symptoms:**
```
{"detail": "Not Found"}
```

**Solution:**
```bash
# Check API is running
curl http://localhost:8000/health

# Check endpoint exists
curl http://localhost:8000/docs

# Verify URL path
# Correct:   /api/v1/accounts
# Incorrect: /api/accounts
```

### 422 Validation Error

**Symptoms:**
```json
{
  "detail": [
    {
      "loc": ["body", "initial_balance"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Solution:**
- Check request body matches API schema
- Verify all required fields are included
- Check data types (string vs number, etc.)

### 500 Internal Server Error

**Symptoms:**
```json
{"detail": "Internal Server Error"}
```

**Solution:**
```bash
# Check server logs
docker-compose logs ultracore-api --tail=100

# Or if running locally:
# Check terminal where `python server.py` is running

# Common causes:
# - Database connection error
# - Kafka connection error
# - Unhandled exception in code
```

---

## 🔐 Authentication Errors

### 401 Unauthorized

**Symptoms:**
```json
{"detail": "Could not validate credentials"}
```

**Solution:**
```bash
# Get access token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Use token in requests
curl http://localhost:8000/api/v1/accounts \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 403 Forbidden

**Symptoms:**
```json
{"detail": "Not enough permissions"}
```

**Solution:**
- Check user has required role (admin, user, etc.)
- Verify tenant_id matches authenticated user's tenant
- Check RBAC permissions

---

## 🚀 Performance Issues

### Slow API Responses

**Symptoms:**
- API requests take >5 seconds
- Timeouts

**Solution:**
```bash
# Check database query performance
# Enable query logging in .env:
LOG_SQL_QUERIES=true

# Check for missing indexes
psql ultracore -c "SELECT * FROM pg_stat_user_tables WHERE idx_scan = 0;"

# Add indexes for slow queries
# Example:
CREATE INDEX idx_accounts_tenant_id ON accounts(tenant_id);

# Check Redis cache hit rate
redis-cli info stats | grep keyspace_hits
```

### High Memory Usage

**Symptoms:**
- Docker containers using >4GB RAM
- System becomes slow

**Solution:**
```bash
# Check Docker memory usage
docker stats

# Limit memory in docker-compose.yml:
services:
  ultracore-api:
    deploy:
      resources:
        limits:
          memory: 2G

# Check for memory leaks
python -m memory_profiler server.py
```

---

## 🔍 Debugging Tips

### Enable Debug Logging

```bash
# In .env:
LOG_LEVEL=DEBUG

# Restart UltraCore
docker-compose restart ultracore-api
```

### Use Python Debugger

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use built-in breakpoint()
breakpoint()
```

### Check Service Health

```bash
# All services
curl http://localhost:8000/health

# PostgreSQL
pg_isready -h localhost -p 5432

# Kafka
kafka-topics.sh --list --bootstrap-server localhost:9092

# Redis
redis-cli ping
```

---

## 🆘 Still Stuck?

### Get Help

1. **Search existing issues:** [GitHub Issues](https://github.com/TuringDynamics3000/UltraCore/issues)
2. **Ask in discussions:** [GitHub Discussions](https://github.com/TuringDynamics3000/UltraCore/discussions)
3. **Open a new issue:** Include:
   - Error message
   - Steps to reproduce
   - Environment (OS, Python version, Docker version)
   - Logs

### Provide Diagnostic Information

```bash
# System information
uname -a
python3.11 --version
docker --version
docker-compose --version

# UltraCore logs
docker-compose logs --tail=200 > ultracore_logs.txt

# Database status
psql ultracore -c "SELECT version();"

# Kafka status
docker exec ultracore-kafka kafka-broker-api-versions --bootstrap-server localhost:9092

# Redis status
redis-cli info server
```

---

## 📚 Additional Resources

- [Quick Start Guide](quick-start.md)
- [Installation Guide](installation.md)
- [Development Setup](../development/setup.md)
- [Architecture Overview](../architecture/overview.md)

---

**Need urgent help?** Email: michael@turingdynamics.ai
