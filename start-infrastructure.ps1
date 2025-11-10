# Start UltraCore Infrastructure

Write-Host "
🚀 Starting UltraCore Infrastructure...
" -ForegroundColor Cyan

# Start services
docker-compose up -d

Write-Host "
⏳ Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host "
✅ Infrastructure Ready!
" -ForegroundColor Green

Write-Host "📊 Services:" -ForegroundColor Cyan
Write-Host "  PostgreSQL:   localhost:5432" -ForegroundColor White
Write-Host "  Kafka:        localhost:9092" -ForegroundColor White
Write-Host "  Kafka UI:     http://localhost:8080" -ForegroundColor White
Write-Host "  Redis:        localhost:6379" -ForegroundColor White
Write-Host "  Prometheus:   http://localhost:9090" -ForegroundColor White
Write-Host "  Grafana:      http://localhost:3000 (admin/admin)" -ForegroundColor White

Write-Host "
🔥 Start UltraCore API:" -ForegroundColor Yellow
Write-Host "  pip install aiokafka" -ForegroundColor Cyan
Write-Host "  $env:PYTHONPATH = 'src'" -ForegroundColor Cyan
Write-Host "  python -m ultracore.main
" -ForegroundColor Cyan
