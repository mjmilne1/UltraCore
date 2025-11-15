# PowerShell Script to Train RL Agents on Windows
# 
# Usage: 
#   .\train_agents_windows.ps1
#
# For overnight training with 500 episodes:
#   Edit train_rl_agents.py and change n_episodes = 100 to n_episodes = 500

Write-Host "=" -NoNewline
Write-Host ("=" * 79)
Write-Host "UltraCore RL Agent Training - Windows"
Write-Host "=" -NoNewline
Write-Host ("=" * 79)
Write-Host ""

# Check Python installation
Write-Host "Checking Python installation..."
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "❌ Python not found in PATH!" -ForegroundColor Red
    Write-Host "Please install Python 3.11+ or add it to PATH" -ForegroundColor Yellow
    exit 1
}

$pythonVersion = python --version
Write-Host "✅ Found: $pythonVersion" -ForegroundColor Green
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path "train_rl_agents.py")) {
    Write-Host "❌ train_rl_agents.py not found!" -ForegroundColor Red
    Write-Host "Please run this script from the UltraCore root directory" -ForegroundColor Yellow
    exit 1
}

# Check if ETF data exists
if (-not (Test-Path "data\etf\historical")) {
    Write-Host "❌ ETF data directory not found!" -ForegroundColor Red
    Write-Host "Please download ETF data first using download_all_etfs.py" -ForegroundColor Yellow
    exit 1
}

$etfCount = (Get-ChildItem "data\etf\historical\*.parquet" -ErrorAction SilentlyContinue).Count
if ($etfCount -eq 0) {
    Write-Host "❌ No ETF data files found!" -ForegroundColor Red
    Write-Host "Please download ETF data first using download_all_etfs.py" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Found $etfCount ETF data files" -ForegroundColor Green
Write-Host ""

# Check required packages
Write-Host "Checking required packages..."
$packages = @("torch", "gymnasium", "pandas", "numpy")
$missingPackages = @()

foreach ($pkg in $packages) {
    $result = python -c "import $pkg" 2>&1
    if ($LASTEXITCODE -ne 0) {
        $missingPackages += $pkg
    }
}

if ($missingPackages.Count -gt 0) {
    Write-Host "❌ Missing packages: $($missingPackages -join ', ')" -ForegroundColor Red
    Write-Host "Installing missing packages..." -ForegroundColor Yellow
    pip install $($missingPackages -join ' ')
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install packages!" -ForegroundColor Red
        exit 1
    }
}

Write-Host "✅ All required packages installed" -ForegroundColor Green
Write-Host ""

# Create models directory if it doesn't exist
if (-not (Test-Path "models\rl_agents")) {
    Write-Host "Creating models directory..."
    New-Item -ItemType Directory -Path "models\rl_agents" -Force | Out-Null
}

# Start training
Write-Host "=" -NoNewline
Write-Host ("=" * 79)
Write-Host "STARTING TRAINING"
Write-Host "=" -NoNewline
Write-Host ("=" * 79)
Write-Host ""
Write-Host "⏰ Started at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host ""
Write-Host "📝 Note: Training progress will be displayed below" -ForegroundColor Yellow
Write-Host "    For overnight training, edit train_rl_agents.py and set n_episodes = 500" -ForegroundColor Yellow
Write-Host ""

# Run training
python train_rl_agents.py

# Check if training succeeded
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "=" -NoNewline
    Write-Host ("=" * 79)
    Write-Host "✅ TRAINING COMPLETED SUCCESSFULLY!" -ForegroundColor Green
    Write-Host "=" -NoNewline
    Write-Host ("=" * 79)
    Write-Host ""
    Write-Host "⏰ Finished at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Trained models saved to: models\rl_agents\" -ForegroundColor Green
    Write-Host "  - alpha_agent.pkl (Q-Learning - POD1 Preservation)" -ForegroundColor Cyan
    Write-Host "  - beta_agent.pkl (Policy Gradient - POD2 Income)" -ForegroundColor Cyan
    Write-Host "  - gamma_agent.pkl (DQN - POD3 Growth)" -ForegroundColor Cyan
    Write-Host "  - delta_agent.pkl (A3C - POD4 Opportunistic)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Test agents with: python end_to_end_example.py" -ForegroundColor White
    Write-Host "  2. Use agents in UltraOptimiser for portfolio optimization" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "=" -NoNewline
    Write-Host ("=" * 79)
    Write-Host "❌ TRAINING FAILED!" -ForegroundColor Red
    Write-Host "=" -NoNewline
    Write-Host ("=" * 79)
    Write-Host ""
    Write-Host "Please check the error messages above" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
