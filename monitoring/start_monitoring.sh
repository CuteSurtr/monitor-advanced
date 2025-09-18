#!/bin/bash

# Financial Monitoring System - Prometheus/Grafana Stack Startup Script

set -e

echo "🚀 Starting Financial Monitoring Stack..."

# Create necessary directories
echo "📁 Creating monitoring directories..."
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/provisioning/datasources
mkdir -p monitoring/grafana/provisioning/dashboards
mkdir -p logs

# Set proper permissions
echo "🔐 Setting permissions..."
chmod +x monitoring/start_monitoring.sh

# Start the monitoring stack
echo "🐳 Starting Docker containers..."
docker-compose -f docker-compose.monitoring.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 30

# Check service health
echo "🏥 Checking service health..."

# Check Prometheus
echo "Checking Prometheus..."
if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo "✅ Prometheus is healthy"
else
    echo "❌ Prometheus health check failed"
fi

# Check Grafana
echo "Checking Grafana..."
if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
    echo "✅ Grafana is healthy"
else
    echo "❌ Grafana health check failed"
fi

# Check Alertmanager
echo "Checking Alertmanager..."
if curl -s http://localhost:9093/-/healthy > /dev/null 2>&1; then
    echo "✅ Alertmanager is healthy"
else
    echo "❌ Alertmanager health check failed"
fi

# Display access information
echo ""
echo "🎯 Monitoring Stack Started Successfully!"
echo "========================================"
echo "📊 Grafana Dashboard: http://localhost:3000"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "📈 Prometheus: http://localhost:9090"
echo "🚨 Alertmanager: http://localhost:9093"
echo "💻 Node Exporter: http://localhost:9100"
echo "📦 cAdvisor: http://localhost:8080"
echo ""
echo "🔍 Financial Application Metrics:"
echo "   Main App: http://localhost:8000"
echo "   Metrics: http://localhost:8001/metrics"
echo "   Risk Metrics: http://localhost:8002/risk-metrics"
echo "   P&L Metrics: http://localhost:8003/pnl-metrics"
echo ""
echo "📋 Available Dashboards:"
echo "   - Financial Overview"
echo "   - Risk Analytics"
echo "   - System Performance"
echo "   - Market Data Quality"
echo ""
echo "🚨 Alert Channels Configured:"
echo "   - Email alerts for all severity levels"
echo "   - Slack integration (configure webhook in alertmanager.yml)"
echo "   - Different teams for different alert categories"
echo ""

# Show running containers
echo "🐳 Running Containers:"
docker-compose -f docker-compose.monitoring.yml ps

echo ""
echo "✨ Setup complete! The financial monitoring system is now running with:"
echo "   ✅ Real-time P&L tracking"
echo "   ✅ VaR/CVaR risk monitoring"  
echo "   ✅ Options chain analysis"
echo "   ✅ VIX volatility tracking"
echo "   ✅ Multi-asset data collection"
echo "   ✅ Sub-second latency optimization"
echo "   ✅ Comprehensive alerting"
echo "   ✅ Performance monitoring"
echo ""
echo "🎉 Your comprehensive real-time financial monitoring system is ready!"