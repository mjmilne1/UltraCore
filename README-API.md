# UltraCore Banking Platform - API Documentation

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Minimal installation (core + API)
pip install -r requirements.txt

# With databases
pip install -r requirements.txt -r requirements-db.txt

# With ML features
pip install -r requirements.txt -r requirements-ml.txt

# Everything
pip install -r requirements.txt -r requirements-db.txt -r requirements-ml.txt -r requirements-monitoring.txt
```

### 2. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 3. Run the Server
```bash
# Simple way
python run.py

# Or with uvicorn directly
uvicorn ultracore.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Access the API

- **API Root**: http://localhost:8000
- **Interactive Docs (Swagger)**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc
- **Health Check**: http://localhost:8000/api/v1/health

## 📚 API Endpoints

### Health & Status
- `GET /api/v1/health` - Health check
- `GET /api/v1/health/detailed` - Detailed system status
- `GET /api/v1/version` - API version

### Customers
- `POST /api/v1/customers` - Create customer
- `GET /api/v1/customers/{id}` - Get customer
- `GET /api/v1/customers` - List customers
- `PATCH /api/v1/customers/{id}` - Update customer
- `DELETE /api/v1/customers/{id}` - Deactivate customer
- `GET /api/v1/customers/{id}/accounts` - Get customer accounts

### Accounts
- `POST /api/v1/accounts` - Open account
- `GET /api/v1/accounts/{id}` - Get account
- `GET /api/v1/accounts` - List accounts
- `GET /api/v1/accounts/{id}/balance` - Get balance
- `POST /api/v1/accounts/{id}/freeze` - Freeze account
- `POST /api/v1/accounts/{id}/unfreeze` - Unfreeze account
- `DELETE /api/v1/accounts/{id}` - Close account

### Transactions
- `POST /api/v1/transactions/deposit` - Make deposit
- `POST /api/v1/transactions/withdraw` - Make withdrawal
- `POST /api/v1/transactions/transfer` - Transfer funds
- `GET /api/v1/transactions/{id}` - Get transaction
- `GET /api/v1/transactions` - List transactions
- `GET /api/v1/transactions/account/{id}/statement` - Get statement

### Payments (Real Payment Rails)
- `POST /api/v1/payments/npp` - NPP (Osko) payment
- `POST /api/v1/payments/bpay` - BPAY bill payment
- `POST /api/v1/payments/swift` - SWIFT international transfer
- `GET /api/v1/payments/{id}` - Get payment status
- `POST /api/v1/payments/npp/payid/register` - Register PayID

### Loans
- `POST /api/v1/loans/apply` - Apply for loan
- `GET /api/v1/loans/{id}` - Get loan
- `GET /api/v1/loans` - List loans
- `POST /api/v1/loans/{id}/approve` - Approve loan
- `POST /api/v1/loans/{id}/disburse` - Disburse loan
- `POST /api/v1/loans/{id}/repay` - Make loan payment
- `GET /api/v1/loans/{id}/schedule` - Get payment schedule

## 💡 Example Usage

### Create a Customer
```bash
curl -X POST "http://localhost:8000/api/v1/customers" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_type": "INDIVIDUAL",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "mobile": "+61400000000",
    "date_of_birth": "1990-01-01"
  }'
```

### Open an Account
```bash
curl -X POST "http://localhost:8000/api/v1/accounts" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": "CUST-123",
    "account_type": "SAVINGS",
    "currency": "AUD",
    "initial_deposit": 1000.00
  }'
```

### Make a Deposit
```bash
curl -X POST "http://localhost:8000/api/v1/transactions/deposit?account_id=ACC-123" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 500.00,
    "description": "Salary deposit"
  }'
```

### NPP Payment
```bash
curl -X POST "http://localhost:8000/api/v1/payments/npp" \
  -H "Content-Type: application/json" \
  -d '{
    "from_account_id": "ACC-123",
    "amount": 100.00,
    "payid": "john@example.com",
    "payid_type": "EMAIL",
    "description": "Payment to John"
  }'
```

## 🔒 Security

- **API Keys**: Coming soon (authentication layer)
- **Rate Limiting**: 60 requests/minute per IP
- **CORS**: Configured for localhost by default
- **Input Validation**: Pydantic models validate all requests

## 📊 Monitoring

Visit `/api/v1/health/detailed` for:
- System metrics (CPU, memory, disk)
- Component status
- Version information

## 🐛 Troubleshooting

### Import Errors
```bash
# Set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/ultracore-working/src"
```

### Port Already in Use
```bash
# Use different port
uvicorn ultracore.api.main:app --port 8001
```

### Module Not Found
```bash
# Install dependencies
pip install -r requirements.txt
```

## 📖 More Information

- See full API documentation at: http://localhost:8000/api/v1/docs
- Interactive testing with Swagger UI
- Complete request/response schemas
- Try it out directly in browser!
