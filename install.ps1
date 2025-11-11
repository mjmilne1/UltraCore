# UltraCore Platform Installation Script

Write-Host "`n📦 INSTALLING ULTRACORE DEPENDENCIES" -ForegroundColor Cyan
Write-Host "=" -repeat 70 -ForegroundColor Cyan

# Check Python version
Write-Host "`n🐍 Checking Python version..." -ForegroundColor Yellow
python --version

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python not found! Please install Python 3.9+" -ForegroundColor Red
    exit 1
}

# Create virtual environment (recommended)
$createVenv = Read-Host "`n💡 Create virtual environment? (recommended) [Y/n]"
if ($createVenv -ne "n" -and $createVenv -ne "N") {
    Write-Host "`n📦 Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
    
    Write-Host "📦 Activating virtual environment..." -ForegroundColor Cyan
    .\venv\Scripts\Activate.ps1
}

# Install dependencies
Write-Host "`n📦 Installing dependencies..." -ForegroundColor Cyan
Write-Host "   This may take 5-10 minutes..." -ForegroundColor Yellow

pip install --upgrade pip

Write-Host "`n1️⃣  Installing core dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt

$installDb = Read-Host "`n💾 Install database dependencies (PostgreSQL, Redis)? [y/N]"
if ($installDb -eq "y" -or $installDb -eq "Y") {
    Write-Host "2️⃣  Installing database dependencies..." -ForegroundColor Cyan
    pip install -r requirements-db.txt
}

$installDev = Read-Host "`n🧪 Install development dependencies (testing, linting)? [y/N]"
if ($installDev -eq "y" -or $installDev -eq "Y") {
    Write-Host "3️⃣  Installing development dependencies..." -ForegroundColor Cyan
    pip install -r requirements-dev.txt
}

Write-Host "`n✅ Installation complete!" -ForegroundColor Green

Write-Host "`n📋 Next steps:" -ForegroundColor Yellow
Write-Host "  1. python init_db.py          # Initialize database" -ForegroundColor Cyan
Write-Host "  2. python run.py              # Start API server" -ForegroundColor Cyan
Write-Host "  3. python test_platform.py    # Run tests" -ForegroundColor Cyan

Write-Host "`n💡 Or run the full test script: .\run_tests.ps1" -ForegroundColor Yellow
