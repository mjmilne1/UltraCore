# 📖 Swagger UI Guide

Interactive API documentation for UltraCore using Swagger UI.

---

## 🚀 Quick Access

**Local Development:**
```
http://localhost:8000/api/v1/docs
```

**Production:**
```
https://ultracore.turingdynamics.ai/api/v1/docs
```

---

## 🎯 What is Swagger UI?

Swagger UI is an interactive API documentation tool that allows you to:

- ✅ **Explore** all available endpoints
- ✅ **Try** API calls directly in your browser
- ✅ **View** request/response schemas
- ✅ **Test** authentication flows
- ✅ **Download** OpenAPI specification

---

## 🔍 Using Swagger UI

### 1. Access Swagger UI

Open your browser and navigate to:
```
http://localhost:8000/api/v1/docs
```

You'll see the interactive API documentation interface.

### 2. Explore Endpoints

- **Expand sections** by clicking on endpoint groups (Customers, Accounts, etc.)
- **View details** by clicking on individual endpoints
- **See schemas** for request bodies and responses

### 3. Authenticate

Before making API calls, you need to authenticate:

1. Click the **"Authorize"** button (top right, lock icon)
2. Enter your credentials or access token
3. Click **"Authorize"**
4. Close the dialog

**For JWT authentication:**
```
Bearer YOUR_ACCESS_TOKEN
```

### 4. Try an Endpoint

1. **Expand an endpoint** (e.g., `GET /api/v1/accounts`)
2. Click **"Try it out"**
3. **Fill in parameters** (if required)
4. Click **"Execute"**
5. **View the response** below

### 5. Copy cURL Command

After executing a request, you can copy the cURL command:

1. Scroll to the **"Curl"** section
2. Click the **"Copy"** button
3. Paste into your terminal

---

## 📋 Example Workflow

### Create a Customer and Account

#### Step 1: Authenticate

1. Click **"Authorize"**
2. Enter your access token:
   ```
   Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
3. Click **"Authorize"**

#### Step 2: Create Customer

1. Expand **"Customers"** section
2. Click on **`POST /api/v1/customers`**
3. Click **"Try it out"**
4. Enter request body:
   ```json
   {
     "tenant_id": "tenant-123",
     "first_name": "John",
     "last_name": "Doe",
     "email": "john.doe@example.com",
     "phone": "+61412345678",
     "date_of_birth": "1990-01-15"
   }
   ```
5. Click **"Execute"**
6. **Copy the customer ID** from the response

#### Step 3: Create Account

1. Expand **"Accounts"** section
2. Click on **`POST /api/v1/accounts`**
3. Click **"Try it out"**
4. Enter request body (use customer ID from Step 2):
   ```json
   {
     "customer_id": "cust-abc123",
     "account_type": "savings",
     "currency": "AUD",
     "initial_balance": 1000.00
   }
   ```
5. Click **"Execute"**
6. **View the account details** in the response

#### Step 4: Check Balance

1. Expand **"Accounts"** section
2. Click on **`GET /api/v1/accounts/{id}/balance`**
3. Click **"Try it out"**
4. Enter the **account ID** from Step 3
5. Click **"Execute"**
6. **View the balance** in the response

---

## 🎨 Swagger UI Features

### Request Body Editor

- **Syntax highlighting** for JSON
- **Auto-completion** for schema fields
- **Validation** before sending request
- **Example values** pre-filled

### Response Viewer

- **Syntax highlighting** for JSON responses
- **Status code** display
- **Response headers** visible
- **Response time** shown

### Schema Explorer

- **Expand/collapse** nested objects
- **View field types** and constraints
- **See required fields** marked with asterisk (*)
- **Example values** for each field

### Download Options

- **Download OpenAPI spec** (JSON or YAML)
- **Export cURL commands**
- **Copy request/response** to clipboard

---

## 🔧 Configuration

### Custom Swagger UI Settings

UltraCore's Swagger UI is configured in `src/ultracore/api/main.py`:

```python
app = FastAPI(
    title="UltraCore Banking Platform",
    description="Enterprise-grade banking infrastructure",
    version="1.0.0",
    docs_url="/api/v1/docs",  # Swagger UI URL
    redoc_url="/api/v1/redoc",  # ReDoc URL
    openapi_url="/api/v1/openapi.json",  # OpenAPI spec URL
)
```

### Disable Swagger UI (Production)

For security, you may want to disable Swagger UI in production:

```python
app = FastAPI(
    title="UltraCore Banking Platform",
    description="Enterprise-grade banking infrastructure",
    version="1.0.0",
    docs_url=None,  # Disable Swagger UI
    redoc_url=None,  # Disable ReDoc
    openapi_url=None,  # Disable OpenAPI spec
)
```

Or use environment variables:

```bash
# .env
ENABLE_DOCS=false
```

```python
settings = get_settings()

app = FastAPI(
    title="UltraCore Banking Platform",
    description="Enterprise-grade banking infrastructure",
    version="1.0.0",
    docs_url="/api/v1/docs" if settings.enable_docs else None,
    redoc_url="/api/v1/redoc" if settings.enable_docs else None,
    openapi_url="/api/v1/openapi.json" if settings.enable_docs else None,
)
```

---

## 🔐 Authentication in Swagger UI

### JWT Bearer Token

1. Get an access token:
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","password":"password"}'
   ```

2. Copy the `access_token` from the response

3. In Swagger UI:
   - Click **"Authorize"**
   - Enter: `Bearer YOUR_ACCESS_TOKEN`
   - Click **"Authorize"**

### API Key

If using API key authentication:

1. In Swagger UI:
   - Click **"Authorize"**
   - Enter your API key
   - Click **"Authorize"**

---

## 🎯 Tips & Tricks

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl + Enter` | Execute request |
| `Ctrl + /` | Focus search |
| `Esc` | Close dialogs |

### Search Endpoints

Use the search box (top right) to quickly find endpoints:
- Search by path: `/accounts`
- Search by tag: `Customers`
- Search by operation: `POST`

### Copy as cURL

After executing a request:
1. Scroll to the **"Curl"** section
2. Click **"Copy"**
3. Paste into terminal or Postman

### Example Values

Click **"Example Value"** next to request body to auto-fill with sample data.

### Response Examples

View multiple response examples:
1. Click on an endpoint
2. Scroll to **"Responses"**
3. Click on different status codes (200, 400, 404, etc.)

---

## 🆚 Swagger UI vs ReDoc

| Feature | Swagger UI | ReDoc |
|---------|------------|-------|
| **Interactive** | ✅ Yes | ❌ No |
| **Try API calls** | ✅ Yes | ❌ No |
| **Clean design** | ⚠️ Functional | ✅ Beautiful |
| **Mobile friendly** | ⚠️ Limited | ✅ Yes |
| **Best for** | Testing | Reading |

**Use Swagger UI for:** Testing and exploring the API  
**Use ReDoc for:** Reading documentation and sharing with clients

---

## 📚 Additional Resources

- **[REST API Documentation](rest-api.md)** - Complete API reference
- **[Code Examples](examples.md)** - Integration examples
- **[Authentication Guide](rest-api.md#authentication)** - Auth setup
- **[Error Handling](rest-api.md#error-handling)** - Error codes

---

## 🆘 Troubleshooting

### Swagger UI Not Loading

**Problem:** Swagger UI shows blank page

**Solution:**
```bash
# Check if API is running
curl http://localhost:8000/health

# Check OpenAPI spec is accessible
curl http://localhost:8000/api/v1/openapi.json

# Restart API
docker-compose restart ultracore-api
```

### Authentication Not Working

**Problem:** "Unauthorized" error after authenticating

**Solution:**
1. Verify token format: `Bearer YOUR_ACCESS_TOKEN` (note the space)
2. Check token expiration
3. Ensure token is valid (test with cURL)

### CORS Errors

**Problem:** CORS errors in browser console

**Solution:**
Update CORS settings in `src/ultracore/api/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

**Happy exploring!** 🚀
