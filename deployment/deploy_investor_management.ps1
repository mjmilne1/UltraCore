# PowerShell Deployment Script for Investor Management Module
#
# Author: Manus AI
# Date:   November 13, 2025

# --- Configuration ---
$RepoUrl = "https://github.com/TuringDynamics3000/UltraCore.git"
$Branch = "investor-management-feature"
$CloneDir = "C:\UltraCore"
$DockerComposeFile = "docker-compose.investor.yml"

# --- Script Body ---

Write-Host "======================================================="
Write-Host "  Deploying UltraCore Investor Management Module"
Write-Host "======================================================="

# 1. Check for Git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "Git is not installed. Please install Git and try again."
    exit
}

# 2. Check for Docker
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is not installed. Please install Docker and try again."
    exit
}

# 3. Clone Repository
if (Test-Path $CloneDir) {
    Write-Host "Repository already exists at $CloneDir. Pulling latest changes..."
    Set-Location $CloneDir
    git pull origin $Branch
} else {
    Write-Host "Cloning repository from $RepoUrl..."
    git clone -b $Branch $RepoUrl $CloneDir
    Set-Location $CloneDir
}

# 4. Build Docker Images
Write-Host "Building Docker images..."
docker-compose -f $DockerComposeFile build

# 5. Start Services
Write-Host "Starting services with Docker Compose..."
docker-compose -f $DockerComposeFile up -d

Write-Host "
Deployment complete!"
Write-Host "Investor Management API should be available at http://localhost:8889"
Write-Host "Kafka UI should be available at http://localhost:9021"
