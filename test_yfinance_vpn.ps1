# Yahoo Finance VPN Test Script (PowerShell)
# Tests if yfinance works with VPN enabled
# Run this from PowerShell on your Windows machine

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "Yahoo Finance Direct Access Test (with VPN)" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 79) -ForegroundColor Cyan
Write-Host "Test time: $(Get-Date)" -ForegroundColor Gray
Write-Host ""

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found in PATH" -ForegroundColor Red
    Write-Host "Please install Python or add it to your PATH" -ForegroundColor Yellow
    exit 1
}

# Check if yfinance is installed
Write-Host "Checking for yfinance library..." -ForegroundColor Gray
$yfinanceCheck = python -c "import yfinance; print('installed')" 2>&1

if ($yfinanceCheck -match "installed") {
    Write-Host "✅ yfinance library found" -ForegroundColor Green
} else {
    Write-Host "❌ yfinance not installed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install with: pip install yfinance" -ForegroundColor Yellow
    Write-Host ""
    $install = Read-Host "Would you like to install it now? (Y/N)"
    if ($install -eq "Y" -or $install -eq "y") {
        Write-Host "Installing yfinance..." -ForegroundColor Yellow
        pip install yfinance
    } else {
        exit 1
    }
}

Write-Host ""
Write-Host "-" -NoNewline -ForegroundColor Cyan
Write-Host ("-" * 79) -ForegroundColor Cyan
Write-Host "Testing ASX ETF data access..." -ForegroundColor Yellow
Write-Host "-" -NoNewline -ForegroundColor Cyan
Write-Host ("-" * 79) -ForegroundColor Cyan

# Python test script
$pythonScript = @"
import yfinance as yf
import json
from datetime import datetime

test_etfs = ['IOZ.AX', 'STW.AX', 'VAS.AX', 'A200.AX', 'NDQ.AX']
results = {'success': [], 'failed': [], 'errors': {}}

for i, symbol in enumerate(test_etfs, 1):
    print(f'\n[{i}/{len(test_etfs)}] Testing {symbol}...')
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='max')
        
        if hist.empty:
            print(f'  ❌ FAILED: No data returned')
            results['failed'].append(symbol)
            results['errors'][symbol] = 'No data returned'
        else:
            info = ticker.info
            name = info.get('longName', 'N/A')
            print(f'  ✅ SUCCESS!')
            print(f'     Name: {name}')
            print(f'     Data points: {len(hist)}')
            print(f'     Date range: {hist.index[0].date()} to {hist.index[-1].date()}')
            print(f'     Latest close: \${hist["Close"].iloc[-1]:.2f}')
            
            results['success'].append({
                'symbol': symbol,
                'name': name,
                'data_points': len(hist),
                'start_date': str(hist.index[0].date()),
                'end_date': str(hist.index[-1].date())
            })
    except Exception as e:
        print(f'  ❌ FAILED: {str(e)}')
        results['failed'].append(symbol)
        results['errors'][symbol] = str(e)

# Summary
print('\n' + '=' * 80)
print('TEST SUMMARY')
print('=' * 80)
print(f'Total tested: {len(test_etfs)}')
print(f'Successful: {len(results["success"])}')
print(f'Failed: {len(results["failed"])}')
print(f'Success rate: {len(results["success"])/len(test_etfs)*100:.1f}%')

if results['success']:
    print('\n✅ Successfully accessed ETFs:')
    for etf in results['success']:
        print(f'  - {etf["symbol"]}: {etf["data_points"]} data points')

if results['failed']:
    print(f'\n❌ Failed ETFs:')
    for symbol in results['failed']:
        print(f'  - {symbol}: {results["errors"][symbol]}')

# Conclusion
print('\n' + '=' * 80)
print('CONCLUSION')
print('=' * 80)

if len(results['success']) == len(test_etfs):
    print('🎉 VPN WORKS! You can now use yfinance directly!')
    print('\nYou have TWO options for data collection:')
    print('  1. Manus Yahoo Finance API (already implemented)')
    print('  2. Direct yfinance (now works with VPN)')
    print('\nBoth are free and will work for your needs.')
elif len(results['success']) > 0:
    print('⚠️  PARTIAL SUCCESS - VPN helps but some issues remain')
    print(f'   {len(results["success"])}/{len(test_etfs)} ETFs accessible')
    print('\nRecommendation: Use Manus API for reliability')
else:
    print('❌ VPN DID NOT RESOLVE THE ISSUE')
    print('\nYahoo Finance is still blocking requests.')
    print('Recommendation: Continue using Manus Yahoo Finance API')

print('\n' + '=' * 80)

# Save results
with open('yfinance_vpn_test_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print('\nResults saved to: yfinance_vpn_test_results.json')
print(json.dumps(results, indent=2))
"@

# Run the Python test
$output = python -c $pythonScript 2>&1

# Display output
Write-Host $output

# Check if results file was created
if (Test-Path "yfinance_vpn_test_results.json") {
    Write-Host ""
    Write-Host "=" -NoNewline -ForegroundColor Cyan
    Write-Host ("=" * 79) -ForegroundColor Cyan
    Write-Host "Test Complete!" -ForegroundColor Green
    Write-Host "=" -NoNewline -ForegroundColor Cyan
    Write-Host ("=" * 79) -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Results saved to: yfinance_vpn_test_results.json" -ForegroundColor Yellow
    Write-Host ""
    
    # Parse results
    $results = Get-Content "yfinance_vpn_test_results.json" | ConvertFrom-Json
    $successCount = $results.success.Count
    $totalCount = $successCount + $results.failed.Count
    
    if ($successCount -eq $totalCount) {
        Write-Host "✅ RECOMMENDATION: VPN works! You can use either:" -ForegroundColor Green
        Write-Host "   - Manus API (already set up)" -ForegroundColor White
        Write-Host "   - Direct yfinance (with VPN active)" -ForegroundColor White
    } elseif ($successCount -gt 0) {
        Write-Host "⚠️  RECOMMENDATION: Use Manus API for reliability" -ForegroundColor Yellow
    } else {
        Write-Host "❌ RECOMMENDATION: Continue using Manus API" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
