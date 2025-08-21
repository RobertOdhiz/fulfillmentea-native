# FulfillmentEA Deployment Script for Windows
# This script deploys the backend and dashboard using Docker

param(
    [string]$Environment = "development",
    [switch]$Production,
    [switch]$Help
)

if ($Help) {
    Write-Host @"
FulfillmentEA Deployment Script

Usage:
    .\deploy.ps1 [options]

Options:
    -Environment <env>     Deployment environment (development, staging, production)
    -Production           Shortcut for production deployment
    -Help                Show this help message

Examples:
    .\deploy.ps1                          # Deploy development
    .\deploy.ps1 -Environment staging     # Deploy staging
    .\deploy.ps1 -Production              # Deploy production
"@
    exit 0
}

if ($Production) {
    $Environment = "production"
}

Write-Host "🚀 Starting FulfillmentEA deployment..." -ForegroundColor Green
Write-Host "Environment: $Environment" -ForegroundColor Yellow

# Check if Docker is running
try {
    docker version | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if docker-compose is available
try {
    docker-compose --version | Out-Null
    Write-Host "✅ Docker Compose is available" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose is not available. Please install Docker Compose." -ForegroundColor Red
    exit 1
}

# Stop existing containers
Write-Host "🛑 Stopping existing containers..." -ForegroundColor Yellow
docker-compose down

# Remove old images (optional)
if ($Production) {
    Write-Host "🧹 Removing old images..." -ForegroundColor Yellow
    docker-compose down --rmi all
}

# Build and start services
if ($Environment -eq "production") {
    Write-Host "🏗️  Building and starting production services..." -ForegroundColor Yellow
    
    # Create necessary directories
    if (!(Test-Path "nginx/ssl")) {
        New-Item -ItemType Directory -Path "nginx/ssl" -Force
        Write-Host "📁 Created nginx/ssl directory" -ForegroundColor Green
    }
    
    if (!(Test-Path "nginx/logs")) {
        New-Item -ItemType Directory -Path "nginx/logs" -Force
        Write-Host "📁 Created nginx/logs directory" -ForegroundColor Green
    }
    
    # Check if SSL certificates exist
    if (!(Test-Path "nginx/ssl/cert.pem") -or !(Test-Path "nginx/ssl/key.pem")) {
        Write-Host "⚠️  SSL certificates not found in nginx/ssl/" -ForegroundColor Yellow
        Write-Host "   Please add your SSL certificates:" -ForegroundColor Yellow
        Write-Host "   - nginx/ssl/cert.pem (SSL certificate)" -ForegroundColor Yellow
        Write-Host "   - nginx/ssl/key.pem (SSL private key)" -ForegroundColor Yellow
        Write-Host "   Then run this script again." -ForegroundColor Yellow
        exit 1
    }
    
    # Start with production profile
    docker-compose --profile production up -d --build
} else {
    Write-Host "🏗️  Building and starting development services..." -ForegroundColor Yellow
    docker-compose up -d --build
}

# Wait for services to be ready
Write-Host "⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Check service health
Write-Host "🔍 Checking service health..." -ForegroundColor Yellow

try {
    $backendHealth = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 10
    Write-Host "✅ Backend is healthy: $($backendHealth.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend health check failed" -ForegroundColor Red
}

try {
    $dashboardHealth = Invoke-RestMethod -Uri "http://localhost:8501/_stcore/health" -Method Get -TimeoutSec 10
    Write-Host "✅ Dashboard is healthy: $($dashboardHealth.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Dashboard health check failed" -ForegroundColor Red
}

# Show service status
Write-Host "📊 Service Status:" -ForegroundColor Green
docker-compose ps

# Show access URLs
Write-Host "🌐 Access URLs:" -ForegroundColor Green
if ($Environment -eq "production") {
    Write-Host "   Dashboard: https://dashboard.fulfillmentea.com" -ForegroundColor Cyan
    Write-Host "   API: https://api.fulfillmentea.com" -ForegroundColor Cyan
    Write-Host "   API Docs: https://api.fulfillmentea.com/docs" -ForegroundColor Cyan
} else {
    Write-Host "   Dashboard: http://localhost:8501" -ForegroundColor Cyan
    Write-Host "   API: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor Cyan
}

Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green

if ($Environment -eq "production") {
    Write-Host "📝 Next steps:" -ForegroundColor Yellow
    Write-Host "   1. Update your DNS records to point to this server:" -ForegroundColor White
    Write-Host "      - api.fulfillmentea.com → [YOUR_SERVER_IP]" -ForegroundColor White
    Write-Host "      - dashboard.fulfillmentea.com → [YOUR_SERVER_IP]" -ForegroundColor White
    Write-Host "   2. Update your mobile app configuration to use the new API domain" -ForegroundColor White
    Write-Host "   3. Test the services from external access" -ForegroundColor White
}
