# InfluxDB Configuration for AI/ML Trading Dashboard

## 🔧 Updated Configuration

Your InfluxDB credentials have been configured throughout the system:

### Connection Details
- **URL**: `http://localhost:8086`
- **Token**: `xEoh_d1wMmj_8sE2ipM1nht5Iq_iJiziHWVGvt9Haplv8QPDuR6oFTRIcX3rT8rG1M6H21tk0sSTv5ujfrPRDg==`
- **Organization**: `stock_monitor`
- **Datasource UID**: `deuydarcrp81sf`

## 📁 Files Updated

The following files have been updated with your credentials:

1. **`scripts/setup_ai_ml_influxdb_buckets.py`** - InfluxDB setup script
2. **`config/config.yaml`** - Main configuration file
3. **`grafana/dashboards/ultimate-professional-trading-dashboard-ai-ml-enhanced.json`** - Dashboard JSON
4. **`AI_ML_DASHBOARD_README.md`** - Documentation

## 🚀 Next Steps

### 1. Setup InfluxDB Buckets
```bash
cd "monitor advanced"
python scripts/setup_ai_ml_influxdb_buckets.py
```

### 2. Start the AI/ML System
```bash
python scripts/start_ai_ml_system.py
```

### 3. Import Dashboard in Grafana
1. Open Grafana: http://localhost:3000
2. Login: admin/admin
3. Go to **Configuration** → **Data Sources** → **Add data source** → **InfluxDB**
4. Configure with your credentials:
   - **URL**: `http://localhost:8086`
   - **Auth**: Enable "Basic auth"
   - **Organization**: `stock_monitor`
   - **Token**: `xEoh_d1wMmj_8sE2ipM1nht5Iq_iJiziHWVGvt9Haplv8QPDuR6oFTRIcX3rT8rG1M6H21tk0sSTv5ujfrPRDg==`
   - **Default Bucket**: `ai_ml_analytics`
5. Click **Save & Test**
6. Import the dashboard JSON file

## 🗄️ Bucket Structure

The system will create these buckets with your credentials:

- **`ai_ml_analytics`**: Model performance and signals (365d retention)
- **`price_predictions`**: AI forecasts (90d retention) 
- **`sentiment_analytics`**: News sentiment (180d retention)
- **`risk_analytics`**: Risk metrics (365d retention)
- **`feature_store`**: ML features (730d retention)

## 🔍 Verification

After setup, verify your configuration:

1. **Check bucket creation**:
   ```bash
   curl -H "Authorization: Token xEoh_d1wMmj_8sE2ipM1nht5Iq_iJiziHWVGvt9Haplv8QPDuR6oFTRIcX3rT8rG1M6H21tk0sSTv5ujfrPRDg==" \
        "http://localhost:8086/api/v2/buckets?org=stock_monitor"
   ```

2. **Test data query**:
   ```bash
   curl -H "Authorization: Token xEoh_d1wMmj_8sE2ipM1nht5Iq_iJiziHWVGvt9Haplv8QPDuR6oFTRIcX3rT8rG1M6H21tk0sSTv5ujfrPRDg==" \
        -H "Content-Type: application/vnd.flux" \
        -d 'from(bucket:"ai_ml_analytics") |> range(start:-1h) |> limit(n:1)' \
        "http://localhost:8086/api/v2/query?org=stock_monitor"
   ```

## ⚠️ Security Notes

- Keep your InfluxDB token secure
- The token provides read/write access to your InfluxDB instance
- Consider rotating tokens periodically in production
- Use environment variables for token storage in production deployments

## 🎯 Ready to Go!

Your AI/ML trading dashboard is now configured with your specific InfluxDB credentials. The system is ready for:

- ✅ Real-time AI predictions
- ✅ Trading signal generation  
- ✅ Sentiment analysis
- ✅ Risk analytics
- ✅ Model performance monitoring

Run the setup script to begin!