# UltraCore Platform Test Runner
# Complete end-to-end testing

Write-Host "`n🧪 ULTRACORE PLATFORM TEST RUNNER" -ForegroundColor Cyan
Write-Host "=" -repeat 70 -ForegroundColor Cyan

# Check if dependencies installed
Write-Host "`n1️⃣  Checking dependencies..." -ForegroundColor Cyan
python -c "import fastapi" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Dependencies not installed!" -ForegroundColor Red
    Write-Host "   Run: .\install.ps1" -ForegroundColor Yellow
    exit 1
}
Write-Host "   ✅ Dependencies installed" -ForegroundColor Green

# Initialize database
Write-Host "`n2️⃣  Initializing database..." -ForegroundColor Cyan
python init_db.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Database initialization failed!" -ForegroundColor Red
    exit 1
}
Write-Host "   ✅ Database initialized" -ForegroundColor Green

# Start API server in background
Write-Host "`n3️⃣  Starting API server..." -ForegroundColor Cyan
$apiProcess = Start-Process -FilePath "python" -ArgumentList "run.py" -PassThru -NoNewWindow
Start-Sleep -Seconds 5

# Check if API is running
Write-Host "`n4️⃣  Checking API health..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -Method GET -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "   ✅ API is running!" -ForegroundColor Green
    }
} catch {
    Write-Host "❌ API not responding!" -ForegroundColor Red
    Stop-Process -Id $apiProcess.Id -Force
    exit 1
}

# Run tests
Write-Host "`n5️⃣  Running test suite..." -ForegroundColor Cyan
Write-Host ""
python test_platform.py

$testResult = $LASTEXITCODE

# Stop API server
Write-Host "`n6️⃣  Stopping API server..." -ForegroundColor Cyan
Stop-Process -Id $apiProcess.Id -Force
Write-Host "   ✅ API server stopped" -ForegroundColor Green

# Summary
Write-Host "`n" -ForegroundColor White
Write-Host "=" -repeat 70 -ForegroundColor Cyan
if ($testResult -eq 0) {
    Write-Host "🎉 ALL TESTS PASSED!" -ForegroundColor Green
    Write-Host "   Your platform is working perfectly!" -ForegroundColor White
} else {
    Write-Host "⚠️  SOME TESTS FAILED" -ForegroundColor Yellow
    Write-Host "   Check the output above for details" -ForegroundColor White
}
Write-Host "=" -repeat 70 -ForegroundColor Cyan

Write-Host "`n💡 To manually test:" -ForegroundColor Yellow
Write-Host "   1. python run.py" -ForegroundColor Cyan
Write-Host "   2. Open http://localhost:8000/api/v1/docs" -ForegroundColor Cyan
Write-Host ""

exit $testResult
