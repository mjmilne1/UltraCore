Write-Host @"

╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║            🇦🇺 ULTRAWEALTH COMPLETE SYSTEM TEST                     ║
║                                                                      ║
║   Testing: DataMesh + ML + RL + AI + MCP + Auto-Update             ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Cyan

$BASE_URL = "http://localhost:8888"
$testResults = @()

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Method = "GET",
        [string]$Uri,
        [object]$Body = $null
    )
    
    Write-Host "`n[$Name]" -ForegroundColor Yellow
    
    try {
        $params = @{
            Uri = "$BASE_URL$Uri"
            Method = $Method
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json)
            $params.ContentType = "application/json"
        }
        
        $result = Invoke-RestMethod @params
        Write-Host "   ✅ PASS" -ForegroundColor Green
        return @{Name=$Name; Status="PASS"; Result=$result}
    }
    catch {
        Write-Host "   ❌ FAIL: $($_.Exception.Message)" -ForegroundColor Red
        return @{Name=$Name; Status="FAIL"; Error=$_.Exception.Message}
    }
}

# ============================================================================
# TEST 1: HEALTH & UNIVERSE
# ============================================================================

Write-Host "`n═══ SECTION 1: HEALTH & UNIVERSE ═══" -ForegroundColor Cyan

$testResults += Test-Endpoint -Name "Health Check" -Uri "/health"
$testResults += Test-Endpoint -Name "Root Endpoint" -Uri "/"
$testResults += Test-Endpoint -Name "ETF Universe" -Uri "/api/v1/universe"
$testResults += Test-Endpoint -Name "Vanguard ETFs" -Uri "/api/v1/universe/provider/Vanguard"
$testResults += Test-Endpoint -Name "Technology ETFs" -Uri "/api/v1/universe/category/Technology"

# ============================================================================
# TEST 2: DATAMESH
# ============================================================================

Write-Host "`n═══ SECTION 2: DATAMESH ═══" -ForegroundColor Cyan

$testResults += Test-Endpoint -Name "DataMesh Status" -Uri "/api/v1/datamesh/status"

$testResults += Test-Endpoint `
    -Name "Ingest ETF Data" `
    -Method "POST" `
    -Uri "/api/v1/datamesh/ingest" `
    -Body @{tickers = @("VAS.AX", "VGS.AX", "NDQ.AX"); period = "2y"}

Start-Sleep -Seconds 3

$testResults += Test-Endpoint -Name "Data Lineage" -Uri "/api/v1/datamesh/lineage/VAS.AX?period=2y"

# ============================================================================
# TEST 3: MACHINE LEARNING
# ============================================================================

Write-Host "`n═══ SECTION 3: MACHINE LEARNING ═══" -ForegroundColor Cyan

$testResults += Test-Endpoint `
    -Name "Train ML Model" `
    -Method "POST" `
    -Uri "/api/v1/ml/train/VAS.AX"

$testResults += Test-Endpoint -Name "ML Prediction" -Uri "/api/v1/ml/predict/VAS.AX"

$testResults += Test-Endpoint `
    -Name "Batch Predictions" `
    -Method "POST" `
    -Uri "/api/v1/ml/batch-predict" `
    -Body @{tickers = @("VAS.AX", "VGS.AX", "NDQ.AX")}

# ============================================================================
# TEST 4: RL PORTFOLIO OPTIMIZATION
# ============================================================================

Write-Host "`n═══ SECTION 4: RL PORTFOLIO OPTIMIZATION ═══" -ForegroundColor Cyan

$testResults += Test-Endpoint `
    -Name "Optimize Portfolio (Moderate)" `
    -Method "POST" `
    -Uri "/api/v1/portfolio/optimize" `
    -Body @{
        tickers = @("VAS.AX", "VGS.AX", "VAF.AX", "NDQ.AX")
        initial_balance = 100000
        risk_tolerance = "moderate"
    }

$testResults += Test-Endpoint `
    -Name "Optimize Portfolio (Conservative)" `
    -Method "POST" `
    -Uri "/api/v1/portfolio/optimize" `
    -Body @{
        tickers = @("VAF.AX", "VGB.AX", "VAS.AX")
        initial_balance = 100000
        risk_tolerance = "conservative"
    }

$testResults += Test-Endpoint `
    -Name "Optimize Portfolio (Aggressive)" `
    -Method "POST" `
    -Uri "/api/v1/portfolio/optimize" `
    -Body @{
        tickers = @("NDQ.AX", "ASIA.AX", "VGS.AX", "VAS.AX")
        initial_balance = 100000
        risk_tolerance = "aggressive"
    }

# ============================================================================
# TEST 5: AGENTIC AI
# ============================================================================

Write-Host "`n═══ SECTION 5: AGENTIC AI ═══" -ForegroundColor Cyan

$testResults += Test-Endpoint `
    -Name "AI Market Analysis" `
    -Method "POST" `
    -Uri "/api/v1/ai/analyze" `
    -Body @{tickers = @("VAS.AX", "VGS.AX", "NDQ.AX", "VAF.AX")}

$testResults += Test-Endpoint `
    -Name "AI Recommendations" `
    -Method "POST" `
    -Uri "/api/v1/ai/recommend" `
    -Body @{
        tickers = @("VAS.AX", "VGS.AX", "VAF.AX")
        current_allocation = @{
            "VAS.AX" = @{weight = 0.40}
            "VGS.AX" = @{weight = 0.40}
            "VAF.AX" = @{weight = 0.20}
        }
        portfolio_value = 100000
    }

$testResults += Test-Endpoint -Name "AI Decision History" -Uri "/api/v1/ai/history?limit=5"

# ============================================================================
# TEST 6: MCP TOOLS
# ============================================================================

Write-Host "`n═══ SECTION 6: MCP TOOLS ═══" -ForegroundColor Cyan

$testResults += Test-Endpoint -Name "List MCP Tools" -Uri "/api/v1/mcp/tools"
$testResults += Test-Endpoint -Name "MCP Get Price" -Uri "/api/v1/mcp/price/VAS.AX"
$testResults += Test-Endpoint -Name "MCP Predict" -Uri "/api/v1/mcp/predict/VGS.AX"

$testResults += Test-Endpoint `
    -Name "MCP Optimize" `
    -Method "POST" `
    -Uri "/api/v1/mcp/optimize" `
    -Body @{
        tickers = @("VAS.AX", "VGS.AX", "VAF.AX")
        initial_balance = 100000
        risk_tolerance = "moderate"
    }

# ============================================================================
# TEST 7: BASIC ETF OPERATIONS
# ============================================================================

Write-Host "`n═══ SECTION 7: BASIC ETF OPERATIONS ═══" -ForegroundColor Cyan

$testResults += Test-Endpoint -Name "Get ETF Price" -Uri "/api/v1/etf/VAS.AX/price"

$testResults += Test-Endpoint `
    -Name "Batch ETF Prices" `
    -Method "POST" `
    -Uri "/api/v1/etf/batch/prices" `
    -Body @{tickers = @("VAS.AX", "VGS.AX", "NDQ.AX", "VAF.AX", "GOLD.AX")}

# ============================================================================
# RESULTS SUMMARY
# ============================================================================

Write-Host "`n`n" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "                    TEST RESULTS SUMMARY                        " -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════════════" -ForegroundColor Green

$passed = ($testResults | Where-Object {$_.Status -eq "PASS"}).Count
$failed = ($testResults | Where-Object {$_.Status -eq "FAIL"}).Count
$total = $testResults.Count

Write-Host "`n📊 Results:" -ForegroundColor Cyan
Write-Host "   Total Tests: $total" -ForegroundColor White
Write-Host "   ✅ Passed: $passed" -ForegroundColor Green
Write-Host "   ❌ Failed: $failed" -ForegroundColor $(if($failed -eq 0){"Green"}else{"Red"})

if ($failed -gt 0) {
    Write-Host "`n❌ Failed Tests:" -ForegroundColor Red
    $testResults | Where-Object {$_.Status -eq "FAIL"} | ForEach-Object {
        Write-Host "   • $($_.Name): $($_.Error)" -ForegroundColor Red
    }
}

Write-Host "`n" -ForegroundColor Cyan
if ($failed -eq 0) {
    Write-Host "🎉 ALL TESTS PASSED! ULTRAWEALTH FULLY OPERATIONAL!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Some tests failed. Check errors above." -ForegroundColor Yellow
}

Write-Host "`n═══════════════════════════════════════════════════════════════`n" -ForegroundColor Green
