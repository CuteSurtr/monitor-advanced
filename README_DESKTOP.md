# 24/7 Global Stock Market Monitor - Desktop Edition

A comprehensive real-time stock market monitoring system optimized for desktop environments with advanced analytics, portfolio management, and enhanced performance.

## 🚀 Quick Start

### One-Click Installation

Choose your operating system and run the installer:

**Windows:**
```batch
scripts\install_windows.bat
```

**macOS:**
```bash
./scripts/install_macos.sh
```

**Linux:**
```bash
./scripts/install_linux.sh
```

**Docker (All Platforms):**
```bash
docker-compose -f docker-compose.desktop.yml up -d
```

## 🖥️ Desktop Features

### Enhanced Performance
- **8GB RAM Support**: Optimized for desktop-class hardware
- **Multi-core Processing**: Utilizes up to 12 worker threads
- **Advanced Caching**: 2GB intelligent cache system
- **GPU Acceleration**: Optional ML model acceleration

### Desktop Integration
- **System Tray**: Background operation with quick access
- **Desktop Notifications**: Real-time alerts and updates
- **Keyboard Shortcuts**: Quick navigation and emergency stops
- **Auto-start**: Optional system startup integration

### Professional Tools
- **Jupyter Lab**: Advanced data analysis environment
- **pgAdmin**: Professional database management
- **Kibana**: Comprehensive log analysis
- **Redis Commander**: Cache management interface

## 📊 What's Different from Raspberry Pi Version?

| Feature | Raspberry Pi | Desktop |
|---------|-------------|---------|
| RAM Usage | 2GB limit | 8GB+ support |
| CPU Cores | 4 workers | 12+ workers |
| Cache Size | 500MB | 2GB |
| Update Frequency | 60s | 30s |
| Concurrent Requests | 10 | 20 |
| Storage | 10GB | 50GB+ |
| ML Models | Basic | Advanced with GPU |
| Additional Services | Basic stack | Full professional suite |

## 🔧 System Requirements

### Minimum
- **OS**: Windows 10, macOS 10.15, Ubuntu 18.04
- **CPU**: Dual-core 2.0GHz
- **RAM**: 4GB
- **Storage**: 10GB
- **Internet**: Broadband connection

### Recommended
- **OS**: Windows 11, macOS 12+, Latest Linux
- **CPU**: Quad-core 3.0GHz+
- **RAM**: 8GB+
- **Storage**: 50GB SSD
- **GPU**: Optional for ML acceleration

## 📈 Enhanced Features

### Advanced Analytics
- **Real-time Technical Analysis**: 15+ indicators
- **ML-based Predictions**: LSTM, Random Forest, XGBoost
- **Sentiment Analysis**: Multi-source news and social media
- **Economic Calendar**: Automated event tracking
- **Correlation Analysis**: Cross-asset relationships

### Portfolio Management
- **Real-time P&L**: Live portfolio tracking
- **Tax Optimization**: Loss harvesting strategies
- **Risk Management**: Advanced risk metrics
- **Rebalancing**: Automated portfolio optimization
- **Backtesting**: Historical strategy testing

### Professional Monitoring
- **Prometheus Metrics**: Comprehensive system monitoring
- **Grafana Dashboards**: Professional visualizations
- **Alert Management**: Multi-channel notifications
- **Performance Analytics**: System optimization insights

## 🌐 Access Points

After installation, access these services:

| Service | URL | Purpose |
|---------|-----|---------|
| **Main Dashboard** | http://localhost:8080 | Primary trading interface |
| **Grafana** | http://localhost:3000 | Professional charts & metrics |
| **Jupyter Lab** | http://localhost:8888 | Data analysis & research |
| **pgAdmin** | http://localhost:5050 | Database management |
| **Prometheus** | http://localhost:9090 | System metrics |
| **Flower** | http://localhost:5555 | Task monitoring |
| **Kibana** | http://localhost:5601 | Log analysis |

## ⚡ Performance Optimization

The desktop version automatically optimizes based on your system:

```python
# Automatic resource detection
CPU Cores: 8 → Workers: 6 (75%)
RAM: 16GB → Cache: 2GB (12.5%)
Storage: SSD → Batch Size: 5000
```

### Manual Optimization

Edit `config/config.desktop.yaml`:

```yaml
performance:
  max_workers: 12          # Increase for more CPU cores
  memory_limit: "16GB"     # Match your system RAM
  max_cache_size: "4GB"    # Increase for better performance
  batch_size: 10000        # Larger batches for SSD storage
```

## 🔐 Security Features

### Enhanced Security (Desktop)
- **Encryption at Rest**: Database and file encryption
- **Secure API Keys**: Encrypted credential storage
- **Audit Logging**: Complete action tracking
- **Access Control**: Multi-user support with roles

### Configuration
```yaml
advanced:
  security:
    encryption_at_rest: true
    secure_api_keys: true
    audit_logging: true
    backup_encryption: true
```

## 📱 Desktop Integration

### System Tray
- **Quick Access**: Right-click for common actions
- **Status Monitoring**: Real-time system health
- **Alert Notifications**: Popup alerts for important events

### Keyboard Shortcuts
- `Ctrl+Shift+D`: Open/close dashboard
- `Ctrl+Shift+P`: Quick portfolio view
- `Ctrl+Shift+A`: View alerts
- `Ctrl+Shift+X`: Emergency stop

### Auto-start (Optional)
```yaml
desktop:
  startup:
    enabled: true
    minimize_to_tray: true
    delay_seconds: 30
```

## 🐳 Docker Desktop Deployment

The easiest way to run on desktop:

```bash
# Start all services
docker-compose -f docker-compose.desktop.yml up -d

# View status
docker-compose -f docker-compose.desktop.yml ps

# View logs
docker-compose -f docker-compose.desktop.yml logs -f stock_monitor

# Stop all services
docker-compose -f docker-compose.desktop.yml down
```

### Docker Services Included
- **PostgreSQL**: Optimized database with 2GB shared buffers
- **Redis**: 1GB cache with LRU eviction
- **InfluxDB**: Time-series data with 2GB memory limit
- **Prometheus**: 90-day retention, 50GB storage
- **Grafana**: Enhanced with plugins
- **Elasticsearch**: Full-text log search
- **Jupyter**: Data science environment

## 🛠️ Development Environment

### Local Development
```bash
# Clone repository
git clone <repository-url>
cd monitor-advanced

# Install development dependencies
pip install -r requirements.desktop.txt

# Start development server
python src/main.py --debug
```

### IDE Integration
- **VS Code**: Recommended with Python extension
- **PyCharm**: Professional Python IDE
- **Jupyter**: Integrated analysis environment

## 📊 Monitoring & Observability

### Metrics Available
- **System Performance**: CPU, Memory, Disk usage
- **Application Metrics**: Request rates, response times
- **Financial Metrics**: Portfolio value, P&L, alerts
- **Data Quality**: API response rates, data freshness

### Alerting
- **Performance Alerts**: System resource warnings
- **Financial Alerts**: Price movements, volatility spikes
- **System Alerts**: Service failures, connectivity issues

## 🔄 Data Management

### Enhanced Data Features
- **Real-time Streaming**: WebSocket connections
- **Historical Data**: 5+ years of market data
- **Alternative Data**: News, sentiment, economic indicators
- **Export Capabilities**: CSV, Excel, Parquet formats

### Data Storage
```
data/
├── market_data/     # Real-time price data
├── historical/      # Historical datasets
├── news/           # News articles and sentiment
├── economic/       # Economic indicators
├── portfolios/     # Portfolio data
└── exports/        # Generated reports
```

## 🚀 Getting Started

1. **Choose Installation Method**
   - Automated script (recommended)
   - Docker deployment
   - Manual installation

2. **Configure API Keys**
   ```bash
   # Edit configuration
   cp config/config.desktop.yaml config/config.yaml
   # Add your API keys to config.yaml
   ```

3. **Start Services**
   ```bash
   # Option 1: Direct start
   python src/main.py
   
   # Option 2: Docker
   docker-compose -f docker-compose.desktop.yml up -d
   ```

4. **Access Dashboard**
   - Open http://localhost:8080
   - Login with default credentials
   - Start monitoring your portfolio

## 📚 Documentation

- **[Desktop Setup Guide](docs/DESKTOP_SETUP.md)**: Comprehensive installation guide
- **[Configuration Reference](docs/CONFIGURATION.md)**: All configuration options
- **[API Documentation](docs/API.md)**: REST API reference
- **[Troubleshooting](docs/TROUBLESHOOTING.md)**: Common issues and solutions

## 🤝 Support

- **Issues**: Report bugs and feature requests
- **Discussions**: Community questions and answers
- **Documentation**: Comprehensive guides and tutorials
- **Examples**: Sample configurations and use cases

## 📄 License

MIT License - see LICENSE file for details.

---

**Ready to start monitoring global markets 24/7 on your desktop? Choose your installation method above and get started in minutes!**