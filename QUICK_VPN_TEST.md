# Quick VPN Test - One Command

## Option 1: Run PowerShell Script (Recommended)

**Step 1:** Open PowerShell as Administrator

**Step 2:** Navigate to UltraCore directory:
```powershell
cd C:\Users\mjmil\UltraCore
```

**Step 3:** Pull latest changes:
```powershell
git pull origin main
```

**Step 4:** Run the test:
```powershell
powershell -ExecutionPolicy Bypass -File .\test_yfinance_vpn.ps1
```

---

## Option 2: Direct Python One-Liner

Open PowerShell and run this single command:

```powershell
python -c "import yfinance as yf; ticker = yf.Ticker('VAS.AX'); hist = ticker.history(period='max'); print(f'SUCCESS: {len(hist)} data points from {hist.index[0].date()} to {hist.index[-1].date()}') if not hist.empty else print('FAILED: No data')"
```

### What This Tests:
- Downloads Vanguard Australian Shares ETF (VAS) data
- If successful: Shows data points and date range
- If failed: Shows "FAILED: No data"

### Expected Results:

**✅ If VPN Works:**
```
SUCCESS: 200 data points from 2009-04-30 to 2025-11-14
```

**❌ If VPN Doesn't Work:**
```
FAILED: No data
```
or
```
Error: 401 Unauthorized
```

---

## Option 3: Even Simpler Test

Just run this in PowerShell:

```powershell
python -c "import yfinance as yf; print('✅ VPN WORKS!' if not yf.Ticker('VAS.AX').history(period='1mo').empty else '❌ VPN FAILED')"
```

This gives you a simple YES/NO answer.

---

## What To Do Based On Results

### ✅ If It Works:
You have two options:
1. **Keep using Manus API** (already working, no VPN needed)
2. **Switch to direct yfinance** (requires VPN to be active)

### ❌ If It Fails:
Continue using Manus API (already collecting data successfully)

---

## Troubleshooting

**If you get "yfinance not found":**
```powershell
pip install yfinance
```

**If you get execution policy error:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**If Python is not found:**
- Ensure Python is installed
- Add Python to PATH
- Or use full path: `C:\Python311\python.exe -c "..."`

---

## Quick Decision Guide

| Test Result | Recommendation |
|-------------|----------------|
| ✅ Works perfectly | Either option is fine - Manus API is already set up |
| ⚠️ Works sometimes | Use Manus API for reliability |
| ❌ Doesn't work | Continue with Manus API (already working) |

**Remember:** You already have a working solution with Manus API collecting 133 ETFs successfully!
