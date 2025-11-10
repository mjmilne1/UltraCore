Write-Host "
🛑 Stopping UltraCore Infrastructure...
" -ForegroundColor Red

docker-compose down

Write-Host "
✅ Infrastructure Stopped
" -ForegroundColor Green

Write-Host "💡 To remove all data: docker-compose down -v
" -ForegroundColor Yellow
