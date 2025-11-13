# PowerShell Deployment Script for UltraCore Additional Modules
#
# Author: Manus AI
# Date: November 13, 2025
#
# This script deploys:
# - Share Accounts & Products Module
# - Close of Business (COB) Processing Module
# - Configuration Management Module

# ============================================================================
# CONFIGURATION
# ============================================================================

$ProjectName = "ultracore-additional"
$DockerComposeFile = "docker-compose.additional.yml"
$EnvFile = ".env.additional"

# ============================================================================
# FUNCTIONS
# ============================================================================

function Write-Host-Info {
    param ([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Host-Success {
    param ([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Host-Error {
    param ([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Check-Prerequisites {
    Write-Host-Info "Checking prerequisites..."
    
    # Check for Docker
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Host-Error "Docker not found. Please install Docker."
        exit 1
    }
    
    # Check for Docker Compose
    if (-not (Get-Command docker-compose -ErrorAction SilentlyContinue)) {
        Write-Host-Error "Docker Compose not found. Please install Docker Compose."
        exit 1
    }
    
    Write-Host-Success "Prerequisites met."
}

function Create-Env-File {
    Write-Host-Info "Creating .env file for additional modules..."
    
    if (Test-Path $EnvFile) {
        Write-Host-Info ".env file already exists. Skipping."
        return
    }
    
    $EnvContent = @"
# Environment variables for Additional Modules

# Kafka
KAFKA_BROKER=kafka:9092

# PostgreSQL
POSTGRES_USER=ultracore
POSTGRES_PASSWORD=ultracore
POSTGRES_DB=additional_db

# API
API_PORT=8890
"@
    
    $EnvContent | Out-File -FilePath $EnvFile -Encoding utf8
    
    Write-Host-Success ".env file created."
}

function Build-Docker-Images {
    Write-Host-Info "Building Docker images for additional modules..."
    
    docker-compose -f $DockerComposeFile -p $ProjectName build
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host-Error "Docker build failed."
        exit 1
    }
    
    Write-Host-Success "Docker images built successfully."
}

function Start-Services {
    Write-Host-Info "Starting additional modules services..."
    
    docker-compose -f $DockerComposeFile -p $ProjectName up -d
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host-Error "Failed to start services."
        exit 1
    }
    
    Write-Host-Success "Additional modules services started."
}

function Stop-Services {
    Write-Host-Info "Stopping additional modules services..."
    
    docker-compose -f $DockerComposeFile -p $ProjectName down
    
    Write-Host-Success "Services stopped."
}

function Show-Status {
    Write-Host-Info "Additional modules status:"
    
    docker-compose -f $DockerComposeFile -p $ProjectName ps
}

function Show-Help {
    Write-Host "Usage: .\deploy_additional_modules.ps1 [command]"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  start    - Build and start all services"
    Write-Host "  stop     - Stop all services"
    Write-Host "  restart  - Restart all services"
    Write-Host "  status   - Show status of services"
    Write-Host "  help     - Show this help message"
    Write-Host ""
}

# ============================================================================
# MAIN SCRIPT
# ============================================================================

param (
    [string]$Command = "start"
)

Check-Prerequisites

switch ($Command) {
    "start" {
        Create-Env-File
        Build-Docker-Images
        Start-Services
        Show-Status
        Write-Host-Success "Additional modules deployed successfully!"
        Write-Host-Info "API available at http://localhost:8890/docs"
    }
    "stop" {
        Stop-Services
    }
    "restart" {
        Stop-Services
        Start-Services
        Show-Status
    }
    "status" {
        Show-Status
    }
    "help" {
        Show-Help
    }
    default {
        Write-Host-Error "Invalid command: $Command"
        Show-Help
    }
}
