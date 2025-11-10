#!/bin/bash
# Start UltraCore Infrastructure

echo "🚀 Starting UltraCore Infrastructure..."

# Start services
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be healthy..."
sleep 30

echo ""
echo "✅ Infrastructure Ready!"
echo ""
echo "📊 Services:"
echo "  PostgreSQL:   localhost:5432"
echo "  Kafka:        localhost:9092"
echo "  Kafka UI:     http://localhost:8080"
echo "  Redis:        localhost:6379"
echo "  Prometheus:   http://localhost:9090"
echo "  Grafana:      http://localhost:3000 (admin/admin)"
echo ""
echo "🔥 Start UltraCore API:"
echo "  pip install aiokafka"
echo "  export PYTHONPATH=src"
echo "  python -m ultracore.main"
echo ""
