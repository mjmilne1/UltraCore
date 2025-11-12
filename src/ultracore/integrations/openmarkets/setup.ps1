# OpenMarkets Integration Setup Script
# This script sets up the complete OpenMarkets integration infrastructure

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("local", "docker", "kubernetes")]
    [string]$Environment = "local"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "OpenMarkets Integration Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
function Test-Prerequisites {
    Write-Host "Checking prerequisites..." -ForegroundColor Yellow
    
    $missing = @()
    
    # Check Python
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "? Python: $pythonVersion" -ForegroundColor Green
    } catch {
        $missing += "Python 3.11+"
    }
    
    # Check Docker (for docker/kubernetes)
    if ($Environment -ne "local") {
        try {
            $dockerVersion = docker --version
            Write-Host "? Docker: $dockerVersion" -ForegroundColor Green
        } catch {
            $missing += "Docker"
        }
    }
    
    # Check kubectl (for kubernetes)
    if ($Environment -eq "kubernetes") {
        try {
            $kubectlVersion = kubectl version --client 2>&1
            Write-Host "? kubectl: $kubectlVersion" -ForegroundColor Green
        } catch {
            $missing += "kubectl"
        }
    }
    
    if ($missing.Count -gt 0) {
        Write-Host "? Missing prerequisites: $($missing -join ', ')" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
}

# Setup local development environment
function Setup-LocalEnvironment {
    Write-Host "Setting up local development environment..." -ForegroundColor Yellow
    
    # Create virtual environment
    Write-Host "Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv venv
    
    # Activate venv
    .\venv\Scripts\Activate.ps1
    
    # Install dependencies
    Write-Host "Installing dependencies..." -ForegroundColor Cyan
    pip install -r requirements.txt
    
    # Create .env file
    if (-not (Test-Path ".env")) {
        Write-Host "Creating .env file..." -ForegroundColor Cyan
        @"
OPENMARKETS_API_KEY=your-api-key-here
OPENMARKETS_API_SECRET=your-api-secret-here
OPENMARKETS_ENVIRONMENT=sandbox
OPENMARKETS_BASE_URL=https://api.openmarkets.com.au/v1
OPENMARKETS_WEBSOCKET_URL=wss://stream.openmarkets.com.au/v1
OPENMARKETS_EVENT_STORE_ENABLED=true
OPENMARKETS_DATA_MESH_ENABLED=true
OPENMARKETS_ML_ENABLED=true
OPENMARKETS_RL_ENABLED=true
OPENMARKETS_MCP_ENABLED=true
"@ | Out-File -FilePath ".env" -Encoding UTF8
        
        Write-Host "? Created .env file (please update with your credentials)" -ForegroundColor Green
    }
    
    Write-Host "? Local environment setup complete!" -ForegroundColor Green
}

# Setup Docker environment
function Setup-DockerEnvironment {
    Write-Host "Setting up Docker environment..." -ForegroundColor Yellow
    
    # Check if docker-compose exists
    if (-not (Test-Path "docker-compose.yml")) {
        Write-Host "? docker-compose.yml not found!" -ForegroundColor Red
        exit 1
    }
    
    # Create .env if not exists
    if (-not (Test-Path ".env")) {
        Setup-LocalEnvironment
    }
    
    # Start services
    Write-Host "Starting Docker services..." -ForegroundColor Cyan
    docker-compose up -d
    
    # Wait for services to be healthy
    Write-Host "Waiting for services to be healthy..." -ForegroundColor Cyan
    Start-Sleep -Seconds 30
    
    # Check service status
    docker-compose ps
    
    Write-Host "? Docker environment setup complete!" -ForegroundColor Green
    Write-Host "Services running at:" -ForegroundColor Cyan
    Write-Host "  - MCP Server: http://localhost:8100" -ForegroundColor White
    Write-Host "  - PostgreSQL: localhost:5432" -ForegroundColor White
    Write-Host "  - Redis: localhost:6379" -ForegroundColor White
    Write-Host "  - Kafka: localhost:9092" -ForegroundColor White
}

# Setup Kubernetes environment
function Setup-KubernetesEnvironment {
    Write-Host "Setting up Kubernetes environment..." -ForegroundColor Yellow
    
    # Check if k8s manifests exist
    if (-not (Test-Path "k8s")) {
        Write-Host "? k8s directory not found!" -ForegroundColor Red
        exit 1
    }
    
    # Create namespace
    Write-Host "Creating namespace..." -ForegroundColor Cyan
    kubectl create namespace ultracore --dry-run=client -o yaml | kubectl apply -f -
    
    # Create secrets
    Write-Host "Creating secrets (please enter your OpenMarkets credentials)..." -ForegroundColor Cyan
    $apiKey = Read-Host "OpenMarkets API Key" -AsSecureString
    $apiSecret = Read-Host "OpenMarkets API Secret" -AsSecureString
    
    $apiKeyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($apiKey)
    )
    $apiSecretPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($apiSecret)
    )
    
    kubectl create secret generic openmarkets-credentials `
        --from-literal=api-key=$apiKeyPlain `
        --from-literal=api-secret=$apiSecretPlain `
        --namespace=ultracore `
        --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply manifests
    Write-Host "Applying Kubernetes manifests..." -ForegroundColor Cyan
    kubectl apply -f k8s/ -n ultracore
    
    # Wait for deployment
    Write-Host "Waiting for deployment to be ready..." -ForegroundColor Cyan
    kubectl rollout status deployment/openmarkets-integration -n ultracore
    
    Write-Host "? Kubernetes environment setup complete!" -ForegroundColor Green
    
    # Get service endpoint
    $service = kubectl get svc openmarkets-service -n ultracore -o json | ConvertFrom-Json
    Write-Host "Service endpoint: $($service.spec.clusterIP):8100" -ForegroundColor Cyan
}

# Run tests
function Run-Tests {
    Write-Host "Running tests..." -ForegroundColor Yellow
    
    if ($Environment -eq "local") {
        .\venv\Scripts\Activate.ps1
    }
    
    pytest tests/unit/integrations/openmarkets/ -v
    pytest tests/integration/openmarkets/ -v --cov=ultracore.integrations.openmarkets
    
    Write-Host "? Tests complete!" -ForegroundColor Green
}

# Main execution
Test-Prerequisites

switch ($Environment) {
    "local" {
        Setup-LocalEnvironment
    }
    "docker" {
        Setup-DockerEnvironment
    }
    "kubernetes" {
        Setup-KubernetesEnvironment
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Update .env with your OpenMarkets credentials" -ForegroundColor White
Write-Host "2. Run tests: pytest tests/" -ForegroundColor White
Write-Host "3. Start development: python -m ultracore.integrations.openmarkets.mcp.server" -ForegroundColor White
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Yellow
Write-Host "- README: integrations/openmarkets/README.md" -ForegroundColor White
Write-Host "- API Docs: http://localhost:8100/docs (when running)" -ForegroundColor White
Write-Host ""
